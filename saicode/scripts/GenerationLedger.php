<?php
declare(strict_types=1);

/** File ownership for the CLI helper; does not bootstrap a framework or connect to a database. */
final class GenerationLedger
{
    private string $project;
    private string $state;
    private array $files;

    public function __construct(string $server, int $id, array $table)
    {
        $server = realpath($server) ?: throw new RuntimeException('宿主目录不存在');
        if ($id < 1) throw new RuntimeException('无效的生成记录 ID');
        $this->project = dirname($server);
        foreach (['namespace','class_name','business_name','generate_path'] as $key) {
            $value = (string)($table[$key] ?? ($key === 'generate_path' ? 'saiadmin-artd' : ''));
            if ($key === 'generate_path' && $value === '') $value = 'saiadmin-artd';
            $pattern = $key === 'generate_path' ? '/^[A-Za-z_][A-Za-z0-9_-]*$/D' : '/^[A-Za-z_][A-Za-z0-9_]*$/D';
            if (!preg_match($pattern, $value)) throw new RuntimeException('不支持的生成路径字段：'.$key);
            $table[$key] = $value;
        }
        if (in_array(strtolower($table['namespace']), ['saiadmin','saicode','saipackage'], true)) throw new RuntimeException('拒绝生成或撤回核心插件');
        $package = (string)($table['package_name'] ?? '');
        if (!preg_match('~^[A-Za-z_][A-Za-z0-9_]*(/[A-Za-z_][A-Za-z0-9_]*)*$~D', $package)) throw new RuntimeException('无效的功能模块路径');
        $template = $table['template'] ?? '';
        if (!in_array($template, ['app','plugin'], true)) throw new RuntimeException('未知的生成模板');
        $front = $this->project.'/'.$table['generate_path'];
        if (!is_dir($front) || realpath($front) !== $front || $front === $server) throw new RuntimeException('前端目录不存在、经过符号链接或与后端相同');
        $base = $template === 'plugin' ? $server.'/plugin/'.$table['namespace'].'/app' : $server.'/app/'.$table['namespace'];
        $admin = $base.($template === 'plugin' ? '/admin' : '');
        $view = $front.'/src/views/plugin/'.$table['namespace'];
        $page = $view.'/'.$package.'/'.$table['business_name'];
        $class = $table['class_name'];
        $this->files = [
            $admin.'/controller/'.$package.'/'.$class.'Controller.php',
            $admin.'/logic/'.$package.'/'.$class.'Logic.php',
            $admin.'/validate/'.$package.'/'.$class.'Validate.php',
            $base.'/model/'.$package.'/'.$class.'.php',
            $page.'/index.vue', $page.'/modules/edit-dialog.vue',
            $page.'/modules/table-search.vue', $page.'/modules/view-dialog.vue',
            $view.'/api/'.$package.'/'.$table['business_name'].'.ts',
        ];
        $this->state = $server.'/runtime/saicode-skill/'.$id.'.json';
        foreach ($this->files as $path) $this->checkPath($path);
        $this->checkPath($this->state);
    }

    public function targets(): array { return $this->files; }

    private function checkPath(string $path): void
    {
        for ($p = $path; $p !== $this->project; $p = dirname($p)) {
            if (is_link($p)) throw new RuntimeException('生成路径不能经过符号链接：'.$p);
            if (dirname($p) === $p) throw new RuntimeException('生成路径越界');
        }
        if (file_exists($path) && !is_file($path)) throw new RuntimeException('目标不是普通文件：'.$path);
    }

    public function read(): ?array
    {
        if (!is_file($this->state)) return null;
        if (is_link($this->state)) throw new RuntimeException('生成记录不能是符号链接');
        $data = json_decode(file_get_contents($this->state), true, 512, JSON_THROW_ON_ERROR);
        if (($data['project'] ?? null) !== $this->project || ($data['targets'] ?? null) !== $this->files) throw new RuntimeException('生成配置已改变，不能套用旧的撤回记录');
        return $data;
    }

    /** Reject overwriting files not owned by a previous successful run, or edited since then. */
    public function preflight(bool $requireRecord = false): array
    {
        $record = $this->read();
        if ($requireRecord && !$record) throw new RuntimeException('没有本工具的生成记录；不能猜测删除历史文件');
        $contents = [];
        foreach ($this->files as $path) {
            $this->checkPath($path);
            if (!is_file($path)) {
                if (isset($record['files'][$path])) throw new RuntimeException('已记录文件缺失，请先核对：'.$path);
                continue;
            }
            $value = file_get_contents($path);
            if ($value === false || ($record['files'][$path] ?? null) !== hash('sha256', $value)) throw new RuntimeException('文件已有内容或生成后被修改，拒绝覆盖/删除：'.$path);
            $contents[$path] = $value;
        }
        return $contents;
    }

    public function record(array $menus): void
    {
        $hashes = [];
        foreach ($this->files as $path) {
            $this->checkPath($path);
            if (is_file($path)) $hashes[$path] = hash_file('sha256', $path);
        }
        if (!$hashes) throw new RuntimeException('生成器没有写入预期文件；请核对宿主模板，不记录假成功');
        $dir = dirname($this->state);
        if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) throw new RuntimeException('无法创建生成记录目录');
        $temp = tempnam($dir, '.ledger-');
        if ($temp === false) throw new RuntimeException('无法创建生成记录');
        try {
            $json = json_encode(['project'=>$this->project,'targets'=>$this->files,'files'=>$hashes,'menus'=>$menus], JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
            if (file_put_contents($temp, $json) !== strlen($json)) throw new RuntimeException('生成记录写入失败');
            chmod($temp, 0600);
            if (!rename($temp, $this->state)) throw new RuntimeException('生成记录替换失败');
        } finally { if (is_file($temp)) unlink($temp); }
    }

    /** Stage files first; restore them if transactional database cleanup fails. */
    public function rollback(callable $cleanup): void
    {
        $before = $this->preflight(true);
        $dir = dirname($this->state).'/rollback-'.bin2hex(random_bytes(8));
        if (!mkdir($dir, 0700, true)) throw new RuntimeException('无法创建撤回备份');
        $moved = [];
        try {
            foreach ($before as $path=>$content) {
                $this->checkPath($path);
                if (file_get_contents($path) !== $content) throw new RuntimeException('撤回期间文件被修改：'.$path);
                $backup = $dir.'/'.hash('sha256', $path).'.bak';
                if (!rename($path, $backup)) throw new RuntimeException('无法备份待撤回文件：'.$path);
                $moved[$path] = $backup;
            }
            $cleanup();
        } catch (Throwable $error) {
            $failures = [];
            foreach ($moved as $path=>$backup) {
                if (file_exists($path) || is_link($path) || !rename($backup, $path)) $failures[] = $path;
            }
            throw new RuntimeException($error->getMessage().($failures ? '；部分文件未恢复，备份位于 '.$dir : '；已恢复本次移动的文件'), 0, $error);
        }
        // Keep backups for recovery; never recursively delete a whole plugin directory.
        if (!unlink($this->state)) throw new RuntimeException('资源已撤回，但生成记录未清理：'.$this->state);
    }
}
