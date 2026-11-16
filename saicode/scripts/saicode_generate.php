#!/usr/bin/env php
<?php
/**
 * SaiCode CLI 代码生成脚本
 * 
 * 用法:
 *   php saicode_generate.php list                                          — 列出已装载的数据表
 *   php saicode_generate.php menus [--parent=ID]                            — 查看系统菜单树(确定 belong_menu_id)
 *   php saicode_generate.php load --table=表名 [--source=mysql]            — 装载数据表
 *   php saicode_generate.php config --id=表ID --namespace=xx --package=xx  — 配置生成选项
 *   php saicode_generate.php columns --id=表ID                             — 查看/修改字段配置
 *   php saicode_generate.php preview --id=表ID                             — 预览生成的代码
 *   php saicode_generate.php generate --id=表ID                            — 生成代码到模块
 *   php saicode_generate.php all --table=表名 --namespace=xx --package=xx  — 一键全流程
 * 
 * 宿主通过 --server-dir、SERVER_DIR 或当前目录探测；--help 不加载宿主
 */

require_once __DIR__.'/GenerationLedger.php';

use plugin\saicode\app\logic\TableLogic;
use plugin\saicode\app\logic\DbLogic;
use plugin\saicode\app\model\Table;
use plugin\saicode\app\model\Column;
use support\think\Db;

try { $args = parseArgs($argv); } catch (Throwable $error) { fwrite(STDERR, '错误：'.$error->getMessage()."\n"); exit(1); }
$command = $args['command'] ?? '';
if (!$command || isset($args['help']) || in_array($command, ['help','-h','--help'], true)) { printUsage(); exit(0); }
$commands = ['list','menus','load','config','columns','relation','preview','generate','rollback','all'];
if (!in_array($command, $commands, true)) { fwrite(STDERR, "未知命令：".$command."\n"); exit(1); }
try {
    if (isset($args['dry-run']) && !in_array($command,['generate','rollback'],true)) throw new RuntimeException('--dry-run 仅用于 generate 或 rollback；其它命令请使用其只读查询形式');
    $requested = $args['server-dir'] ?? getenv('SERVER_DIR');
    $candidates = $requested ? [$requested] : [getcwd(), getcwd().'/server'];
    $serverDir = null;
    foreach ($candidates as $candidate) {
        $real = realpath((string)$candidate);
        if ($real && is_file($real.'/vendor/autoload.php') && is_file($real.'/support/bootstrap.php') && is_dir($real.'/plugin/saicode')) { $serverDir=$real; break; }
    }
    if (!$serverDir) throw new RuntimeException('找不到准备好的 SaiCode 宿主，请指定 --server-dir /path/to/server（需要 vendor、support/bootstrap.php 和 plugin/saicode）');
    chdir($serverDir);
    require_once $serverDir.'/vendor/autoload.php';
    require_once $serverDir.'/support/bootstrap.php';
    $dispatch = ['list'=>'cmdList','menus'=>'cmdMenus','load'=>'cmdLoad','config'=>'cmdConfig','columns'=>'cmdColumns','relation'=>'cmdRelation','preview'=>'cmdPreview','generate'=>'cmdGenerate','rollback'=>'cmdRollback','all'=>'cmdAll'];
    // One helper writer per host; preview/read commands never create runtime files.
    $lock = null;
    $mutates = in_array($command, ['load','generate','all'], true) || ($command==='rollback' && isset($args['apply'])) || ($command==='config' && count(array_diff(array_keys($args), ['command','id','server-dir']))>0) || ($command==='columns' && isset($args['set'])) || ($command==='relation' && (isset($args['add']) || isset($args['del'])));
    if ($mutates && !isset($args['dry-run'])) {
        $dir=$serverDir.'/runtime/saicode-skill';
        if (!is_dir($dir) && !mkdir($dir,0700,true) && !is_dir($dir)) throw new RuntimeException('无法创建 CLI 锁目录');
        $lock=fopen($dir.'/lock','c');
        if (!$lock || !flock($lock, LOCK_EX)) throw new RuntimeException('无法锁定 SaiCode CLI');
    }
    try { $dispatch[$command]($args); }
    finally { if ($lock) { flock($lock,LOCK_UN); fclose($lock); } }
} catch (Throwable $error) { fwrite(STDERR, '错误：'.$error->getMessage()."\n"); exit(1); }

// ========== 命令实现 ==========

/**
 * 列出已装载的数据表
 */
function cmdList(): void
{
    $tables = Table::select()->toArray();
    if (empty($tables)) {
        echo "暂无已装载的数据表\n";
        return;
    }
    echo str_pad('ID', 6) . str_pad('表名', 30) . str_pad('类名', 25) . str_pad('命名空间', 20) . str_pad('模块', 15) . "备注\n";
    echo str_repeat('-', 110) . "\n";
    foreach ($tables as $t) {
        echo str_pad($t['id'], 6)
            . str_pad($t['table_name'], 30)
            . str_pad($t['class_name'], 25)
            . str_pad($t['namespace'] ?? '-', 20)
            . str_pad($t['package_name'] ?? '-', 15)
            . ($t['table_comment'] ?? '') . "\n";
    }
    echo "\n共 " . count($tables) . " 张表\n";
}

/**
 * 查看系统菜单树（用于确定 belong_menu_id）
 */
function cmdMenus(array $args): void
{
    $parentId = $args['parent'] ?? null;

    if ($parentId !== null) {
        // 显示指定父菜单的子菜单
        $menus = Db::table('sa_system_menu')
            ->where('parent_id', $parentId)
            ->whereNull('delete_time')
            ->where('type', 'in', [1, 2])  // 只显示目录和菜单
            ->order('sort', 'asc')
            ->select();
    } else {
        // 显示顶级菜单
        $menus = Db::table('sa_system_menu')
            ->where('parent_id', 0)
            ->whereNull('delete_time')
            ->where('type', 'in', [1, 2])
            ->order('sort', 'asc')
            ->select();
    }

    if (empty($menus)) {
        echo "无菜单数据" . ($parentId !== null ? " (parent_id={$parentId})" : '') . "\n";
        return;
    }

    $typeMap = [1 => '目录', 2 => '菜单', 3 => '权限'];
    echo str_pad('ID', 8) . str_pad('名称', 25) . str_pad('类型', 10) . str_pad('路径', 30) . "组件\n";
    echo str_repeat('-', 110) . "\n";
    foreach ($menus as $m) {
        echo str_pad($m['id'], 8)
            . str_pad($m['name'], 25)
            . str_pad($typeMap[$m['type']] ?? '-', 10)
            . str_pad($m['path'] ?? '-', 30)
            . ($m['component'] ?? '-') . "\n";

        // 显示子菜单
        $children = Db::table('sa_system_menu')
            ->where('parent_id', $m['id'])
            ->whereNull('delete_time')
            ->where('type', 'in', [1, 2])
            ->order('sort', 'asc')
            ->select();
        foreach ($children as $c) {
            echo '  ' . str_pad($c['id'], 6)
                . str_pad('└─ ' . $c['name'], 23)
                . str_pad($typeMap[$c['type']] ?? '-', 10)
                . str_pad($c['path'] ?? '-', 30)
                . ($c['component'] ?? '-') . "\n";
        }
    }
    echo "\n提示: 使用 --parent=ID 查看指定菜单的子菜单\n";
    echo "将目标菜单的 ID 用作 --belong_menu_id 参数\n";
}

/**
 * 装载数据表
 */
function cmdLoad(array $args): int
{
    $tableName = $args['table'] ?? '';
    $source = $args['source'] ?? 'mysql';

    if (empty($tableName)) {
        fwrite(STDERR, "错误: 缺少 --table 参数\n");
        throw new RuntimeException('缺少 --table 参数');
    }

    // 检查表是否已装载
    $existing = Table::where('table_name', $tableName)->where('source', $source)->findOrEmpty();
    if (!$existing->isEmpty()) {
        echo "表 {$tableName} 已存在 (ID: {$existing->id})，跳过装载\n";
        return (int)$existing->id;
    }

    $dbLogic = new DbLogic();
    // 检查表是否存在
    $tableInfo = null;
    if (!empty($source)) {
        $connection = Db::connect($source);
        if ($connection->getConfig('type') !== 'mysql') throw new RuntimeException('此辅助 CLI 的 load 仅支持 MySQL；其它数据库使用宿主生成器的已验证装载接口');
        $list = $connection->query('show table status where name=:name', ['name' => $tableName]);
    } else {
        $list = Db::query('show table status where name=:name', ['name' => $tableName]);
    }
    if (empty($list)) {
        fwrite(STDERR, "错误: 数据表 {$tableName} 不存在于数据源 {$source}\n");
        throw new RuntimeException('数据源中没有目标表');
    }
    $tableInfo = [
        'name' => $list[0]['Name'],
        'comment' => $list[0]['Comment'],
    ];

    $logic = new TableLogic();
    $logic->loadTable([$tableInfo], $source);

    // 获取刚装载的表ID
    $loaded = Table::where('table_name', $tableName)->where('source', $source)->findOrEmpty();
    echo "✅ 成功装载表: {$tableName} (ID: {$loaded->id})\n";
    return (int)$loaded->id;
}

/**
 * 配置生成选项
 */
function cmdConfig(array $args): void
{
    $id = $args['id'] ?? '';
    if (empty($id)) {
        fwrite(STDERR, "错误: 缺少 --id 参数\n");
        exit(1);
    }

    $table = Table::findOrEmpty($id);
    if ($table->isEmpty()) {
        fwrite(STDERR, "错误: 未找到 ID={$id} 的表记录\n");
        exit(1);
    }

    $updateData = [];
    $configFields = [
        'namespace'      => '应用名称',
        'package_name'   => '功能模块',
        'template'       => '应用类型(app/plugin)',
        'tpl_category'   => '模板类型(single/tree)',
        'generate_menus' => '生成功能',
        'generate_path'  => '前端项目目录',
        'belong_menu_id' => '上级菜单ID',
        'menu_name'      => '菜单名称',
        'business_name'  => '业务名称',
        'component_type' => '组件类型(1=弹窗/2=抽屉/3=标签页)',
        'form_width'     => '表单弹窗宽度',
        'is_full'        => '是否全屏(1=否/2=是)',
        'span'           => '表单栅格宽度(1-24)',
    ];

    if (isset($args['namespace']) && in_array(strtolower((string)$args['namespace']), ['saiadmin','saicode','saipackage'], true)) throw new RuntimeException('不能将业务代码生成到核心插件');

    // 处理 package 缩写参数
    if (isset($args['package'])) {
        $args['package_name'] = $args['package'];
    }
    // 处理 menu 缩写参数
    if (isset($args['menu'])) {
        $args['belong_menu_id'] = $args['menu'];
    }

    foreach ($configFields as $field => $label) {
        if (isset($args[$field]) && $args[$field] !== '') {
            $updateData[$field] = $args[$field];
        }
    }

    if (empty($updateData)) {
        echo "当前配置:\n";
        foreach ($configFields as $field => $label) {
            echo "  {$label} ({$field}): " . ($table->$field ?? '-') . "\n";
        }
        echo "\n使用 --字段名=值 修改配置\n";
        return;
    }

    Table::where('id', $id)->update($updateData);
    echo "✅ 配置已更新:\n";
    foreach ($updateData as $field => $value) {
        $label = $configFields[$field] ?? $field;
        echo "  {$label}: {$value}\n";
    }
}

/**
 * 预览生成的代码
 */
function cmdPreview(array $args): void
{
    $id = $args['id'] ?? '';
    if (empty($id)) {
        fwrite(STDERR, "错误: 缺少 --id 参数\n");
        exit(1);
    }

    $logic = new TableLogic();
    $data = $logic->preview($id);

    foreach ($data as $item) {
        echo "\n" . str_repeat('=', 60) . "\n";
        echo "📄 {$item['tab_name']}\n";
        echo str_repeat('=', 60) . "\n";
        echo $item['code'] . "\n";
    }
}

/**
 * 查看/修改已装载表的字段配置
 */
function cmdColumns(array $args): void
{
    $id = $args['id'] ?? '';
    if (empty($id)) {
        fwrite(STDERR, "错误: 缺少 --id 参数 (saicode_table 的 ID)\n");
        exit(1);
    }

    $columns = Column::where('table_id', $id)
        ->order('list_sort', 'asc')
        ->select()
        ->toArray();

    if (empty($columns)) {
        echo "未找到 table_id={$id} 的字段信息\n";
        return;
    }

    // 如果有 --set 参数，批量修改字段属性
    // 格式: --set=column_name:属性=值,属性=值
    if (isset($args['set'])) {
        $setParts = explode(':', $args['set'], 2);
        if (count($setParts) !== 2) {
            fwrite(STDERR, "错误: --set 格式为 字段名:属性=值,属性=值\n");
            fwrite(STDERR, "示例: --set=status:view_type=select,dict_type=data_status\n");
            exit(1);
        }
        $colName = $setParts[0];
        $attrs = [];
        foreach (explode(',', $setParts[1]) as $pair) {
            $kv = explode('=', $pair, 2);
            if (count($kv) === 2) {
                $attrs[$kv[0]] = $kv[1];
            }
        }
        $col = Column::where('table_id', $id)->where('column_name', $colName)->findOrEmpty();
        if ($col->isEmpty()) {
            fwrite(STDERR, "错误: 未找到字段 {$colName}\n");
            exit(1);
        }
        Column::where('id', $col->id)->update($attrs);
        echo "✅ 字段 {$colName} 已更新: " . json_encode($attrs, JSON_UNESCAPED_UNICODE) . "\n";
        return;
    }

    // 显示字段列表
    echo "表 ID={$id} 的字段配置:\n\n";
    echo str_pad('字段名', 22) . str_pad('类型', 12) . str_pad('注释', 18)
        . str_pad('视图组件', 15) . str_pad('字典', 14)
        . str_pad('新增', 5) . str_pad('编辑', 5) . str_pad('列表', 5)
        . str_pad('搜索', 5) . str_pad('必填', 5) . "查询方式\n";
    echo str_repeat('-', 130) . "\n";

    $yn = function ($v) {
        return $v == 2 ? '✓' : '-';
    };
    foreach ($columns as $c) {
        echo str_pad($c['column_name'], 22)
            . str_pad($c['column_type'], 12)
            . str_pad(mb_substr($c['column_comment'] ?? '', 0, 8), 18)
            . str_pad($c['view_type'] ?? 'input', 15)
            . str_pad($c['dict_type'] ?? '-', 14)
            . str_pad($yn($c['is_insert']), 5)
            . str_pad($yn($c['is_edit']), 5)
            . str_pad($yn($c['is_list']), 5)
            . str_pad($yn($c['is_query']), 5)
            . str_pad($yn($c['is_required']), 5)
            . ($c['query_type'] ?? '-') . "\n";
    }
    echo "\n可修改属性: view_type, dict_type, is_insert(1/2), is_edit(1/2), is_list(1/2), is_query(1/2), is_required(1/2), query_type\n";
    echo "修改示例: --set=status:view_type=select,dict_type=data_status\n";
}

/**
 * 查看/添加模型关联配置
 */
function cmdRelation(array $args): void
{
    $id = $args['id'] ?? '';
    if (empty($id)) {
        fwrite(STDERR, "错误: 缺少 --id 参数\n");
        exit(1);
    }

    $table = Table::findOrEmpty($id);
    if ($table->isEmpty()) {
        fwrite(STDERR, "错误: 未找到 ID={$id} 的表记录\n");
        exit(1);
    }

    $options = $table->options ? (is_string($table->options) ? json_decode($table->options, true) : $table->options) : [];
    $relations = $options['relations'] ?? [];

    // 添加关联: --add --type=belongsTo --name=category --model=CategoryModel --localKey=category_id --foreignKey=id
    if (isset($args['add'])) {
        $type = $args['type'] ?? '';
        $name = $args['name'] ?? '';
        $model = $args['model'] ?? '';
        $localKey = $args['localKey'] ?? $args['local_key'] ?? '';
        $foreignKey = $args['foreignKey'] ?? $args['foreign_key'] ?? '';
        $midTable = $args['table'] ?? $args['mid_table'] ?? '';

        if (empty($type) || empty($name) || empty($model)) {
            fwrite(STDERR, "错误: --add 需要 --type, --name, --model 参数\n");
            fwrite(STDERR, "示例: --add --type=belongsTo --name=category --model=app\\model\\Category --localKey=category_id --foreignKey=id\n");
            exit(1);
        }

        $validTypes = ['hasOne', 'hasMany', 'belongsTo', 'belongsToMany'];
        if (!in_array($type, $validTypes)) {
            fwrite(STDERR, "错误: type 必须是 " . implode('/', $validTypes) . "\n");
            exit(1);
        }

        $relations[] = [
            'type' => $type,
            'name' => $name,
            'model' => $model,
            'localKey' => $localKey,
            'foreignKey' => $foreignKey,
            'table' => $midTable,
        ];
        $options['relations'] = $relations;
        Table::where('id', $id)->update(['options' => json_encode($options, JSON_UNESCAPED_UNICODE)]);
        echo "✅ 添加关联成功: {$name} ({$type}) -> {$model}\n";
        return;
    }

    // 删除关联: --del=name
    if (isset($args['del'])) {
        $delName = $args['del'];
        $newRelations = array_values(array_filter($relations, fn($r) => $r['name'] !== $delName));
        $options['relations'] = $newRelations;
        Table::where('id', $id)->update(['options' => json_encode($options, JSON_UNESCAPED_UNICODE)]);
        echo "✅ 已删除关联: {$delName}\n";
        return;
    }

    // 显示关联列表
    if (empty($relations)) {
        echo "表 ID={$id} 暂无关联配置\n";
        echo "\n添加示例: --add --type=belongsTo --name=category --model=CategoryModel --localKey=category_id --foreignKey=id\n";
        return;
    }

    echo "表 ID={$id} 的关联配置:\n\n";
    echo str_pad('名称', 18) . str_pad('类型', 18) . str_pad('关联模型', 35) . str_pad('本地键', 18) . str_pad('外键', 18) . "中间表\n";
    echo str_repeat('-', 130) . "\n";
    foreach ($relations as $r) {
        echo str_pad($r['name'] ?? '-', 18)
            . str_pad($r['type'] ?? '-', 18)
            . str_pad($r['model'] ?? '-', 35)
            . str_pad($r['localKey'] ?? '-', 18)
            . str_pad($r['foreignKey'] ?? '-', 18)
            . ($r['table'] ?? '-') . "\n";
    }
    echo "\n删除关联: --del=关联名称\n";
}

/**
 * 撤回生成：删除生成的文件 + 菜单权限
 */
function menuSnapshot(int $id): array
{
    $parents = Db::table('sa_system_menu')->where('generate_id', $id)->select()->toArray();
    $rows = []; $queue = $parents;
    while ($queue) {
        $row = array_shift($queue); $key=(int)$row['id'];
        if (isset($rows[$key])) continue;
        ksort($row); $rows[$key]=$row;
        foreach (Db::table('sa_system_menu')->where('parent_id',$key)->select()->toArray() as $child) $queue[]=$child;
    }
    ksort($rows); return array_values($rows);
}

function cmdRollback(array $args): void
{
    $id=(int)($args['id']??0);
    if ($id<1) throw new RuntimeException('缺少有效 --id');
    $table=Table::findOrEmpty($id);
    if ($table->isEmpty()) throw new RuntimeException('生成配置不存在');
    $ledger=new GenerationLedger(base_path(),$id,$table->toArray());
    foreach ($ledger->targets() as $file) echo "撤回候选：".$file."\n";
    if (!isset($args['apply']) || isset($args['dry-run'])) { echo "只读预览；执行已核对的撤回时加 --apply。只支持本工具已记录且未被修改的文件和菜单。\n"; return; }
    $ledger->preflight(true);
    $record=$ledger->read();
    if (menuSnapshot($id)!==$record['menus']) throw new RuntimeException('生成后的菜单被修改，拒绝删除');
    $ledger->rollback(static function() use ($id,$record,$args) {
        Db::transaction(static function() use ($id,$record,$args) {
            if (menuSnapshot($id)!==$record['menus']) throw new RuntimeException('撤回期间菜单发生变化');
            $ids=array_column($record['menus'],'id');
            if ($ids) Db::table('sa_system_menu')->whereIn('id',$ids)->delete();
            if (isset($args['clean'])) { Column::where('table_id',$id)->delete(); Table::where('id',$id)->delete(); }
        });
    });
    echo "撤回完成；文件备份保留在 runtime/saicode-skill，按宿主约定刷新权限缓存及重载服务。\n";
}

/**
 * 生成代码到模块
 */
function cmdGenerate(array $args): void
{
    $id = $args['id'] ?? '';
    if (empty($id)) {
        fwrite(STDERR, "错误: 缺少 --id 参数\n");
        exit(1);
    }

    // 检查必要配置
    $table = Table::findOrEmpty($id);
    if ($table->isEmpty()) {
        fwrite(STDERR, "错误: 未找到 ID={$id} 的表记录\n");
        exit(1);
    }
    if (empty($table->namespace)) {
        fwrite(STDERR, "错误: 请先配置 namespace (应用名称)\n");
        exit(1);
    }
    if (empty($table->package_name)) {
        fwrite(STDERR, "错误: 请先配置 package_name (功能模块)\n");
        exit(1);
    }

    $ledger = new GenerationLedger(base_path(), (int)$id, $table->toArray());
    $ledger->preflight();
    $previous = $ledger->read();
    $menusBefore = menuSnapshot((int)$id);
    if ($previous ? $menusBefore !== $previous['menus'] : (bool)$menusBefore) throw new RuntimeException('菜单已有内容或生成后被修改，拒绝覆盖');
    if (isset($args['dry-run'])) {
        foreach ($ledger->targets() as $path) echo "生成候选：".$path."\n";
        echo "只读预检；未写入文件或菜单。\n"; return;
    }
    $logic = new TableLogic();
    $logic->generateFile($id);
    $ledger->record(menuSnapshot((int)$id));

    echo "✅ 代码生成成功!\n";
    echo "  表名: {$table->table_name}\n";
    echo "  类名: {$table->class_name}\n";

    if ($table->template === 'plugin') {
        echo "  后端路径: plugin/{$table->namespace}/app/admin/...\n";
    } else {
        echo "  后端路径: app/{$table->namespace}/...\n";
    }
    $generatePath = $table->generate_path ?: 'saiadmin-artd';
    echo "  前端路径: {$generatePath}/src/views/plugin/{$table->namespace}/...\n";
    echo "  菜单权限: 已自动创建\n";
}

/**
 * 一键全流程: load + config + generate
 */
function cmdAll(array $args): void
{
    if (isset($args['dry-run'])) throw new RuntimeException('all 会装载/修改生成配置；只读预检请使用已配置 ID 的 generate --dry-run 或 preview');
    $tableName = $args['table'] ?? '';
    if (empty($tableName)) {
        fwrite(STDERR, "错误: 缺少 --table 参数\n");
        exit(1);
    }

    // 必须有 namespace 和 package_name
    $namespace = $args['namespace'] ?? '';
    $packageName = $args['package_name'] ?? $args['package'] ?? '';
    if (empty($namespace)) {
        fwrite(STDERR, "错误: 缺少 --namespace 参数\n");
        exit(1);
    }
    if (empty($packageName)) {
        fwrite(STDERR, "错误: 缺少 --package 参数\n");
        exit(1);
    }

    $source = $args['source'] ?? 'mysql';

    // Step 1: Load
    echo ">>> 步骤 1/3: 装载数据表 {$tableName}\n";
    $id = cmdLoad($args);
    if ($id <= 0) {
        exit(1);
    }

    // Step 2: Config
    echo "\n>>> 步骤 2/3: 配置生成选项\n";
    $args['id'] = $id;
    $args['package_name'] = $packageName;
    cmdConfig($args);

    // Step 3: Generate
    echo "\n>>> 步骤 3/3: 生成代码到模块\n";
    cmdGenerate($args);

    echo "\n🎉 全流程完成!\n";
}

// ========== 工具函数 ==========

function parseArgs(array $argv): array
{
    $result=[];
    for ($i=1;$i<count($argv);$i++) {
        $arg=$argv[$i];
        if ($arg==='-h') { $result['help']=true; continue; }
        if (str_starts_with($arg,'--')) {
            $parts=explode('=',substr($arg,2),2);$key=$parts[0];
            if (isset($parts[1])) $value=$parts[1];
            elseif (in_array($key,['help','apply','dry-run','clean','add'],true)) $value=true;
            elseif (isset($argv[$i+1]) && !str_starts_with($argv[$i+1],'--')) $value=$argv[++$i];
            else throw new InvalidArgumentException('选项需要值：--'.$key);
            $result[$key]=$value;
        } elseif (!isset($result['command'])) $result['command']=$arg;
        else throw new InvalidArgumentException('未识别参数：'.$arg);
    }
    return $result;
}

function printUsage(): void
{
    echo <<<USAGE
SaiCode CLI 代码生成脚本

用法:
  php saicode_generate.php <command> [options]

命令:
  list                              列出已装载的数据表
  menus   [--parent=ID]             查看系统菜单树(确定 belong_menu_id)
  load    --table=表名              装载数据表到 saicode 系统
  config  --id=表ID                 查看/修改生成配置
  columns --id=表ID                 查看已装载表的字段配置
  columns --id=表ID --set=字段:k=v  修改字段属性
  relation --id=表ID                查看关联配置
  relation --id=表ID --add ...      添加模型关联
  relation --id=表ID --del=名称     删除模型关联
  preview --id=表ID                 预览生成的代码
  generate --id=表ID                生成代码到模块(文件+菜单)
  rollback --id=表ID                预览撤回；加 --apply 才执行所有权检查后的清理
  rollback --id=表ID --apply --clean 撤回并清理 saicode 记录
  all     --table=表名 ...          一键全流程(load+config+generate)

通用选项:
  --server-dir=/path/to/server       显式宿主目录；也可使用 SERVER_DIR 或当前目录探测
  --dry-run                         预检 generate / rollback，不写文件或菜单
  --apply                           明确执行 rollback（默认只读预览）
  --source=mysql                    数据源名称 (默认: mysql；load 当前只支持 MySQL)
  --namespace=example              应用名称
  --package=system                  功能模块分组
  --template=plugin                 应用类型: app 或 plugin (默认: app)
  --generate_path=saiadmin-artd     前端项目目录名 (默认: saiadmin-artd)
  --belong_menu_id=ID               从 menus 查询的上级菜单 ID
  --generate_menus=index,save,...   生成的功能列表
  --tpl_category=single             模板类型: single 或 tree
  --component_type=1                组件类型: 1=弹窗 2=抽屉 3=标签页
  --form_width=600                  表单弹窗宽度(px)
  --menu_name=菜单名                菜单显示名称(默认用表注释)

示例:
  # 先查看菜单树，确定上级菜单ID
  php saicode_generate.php menus
  php saicode_generate.php menus --parent=1003

  # 一键为 sa_member 表生成 saiuser 插件的 member 模块代码
  php saicode_generate.php all --table=sa_member --namespace=saiuser --package=member --template=plugin --belong_menu_id=1003

  # 分步操作
  php saicode_generate.php load --table=sa_member
  php saicode_generate.php config --id=1 --namespace=saiuser --package=member --template=plugin
  php saicode_generate.php columns --id=1
  php saicode_generate.php columns --id=1 --set=status:view_type=select,dict_type=data_status
  php saicode_generate.php relation --id=1 --add --type=belongsTo --name=level --model=MemberLevel --localKey=member_level_id --foreignKey=id
  php saicode_generate.php generate --id=1

USAGE;
}
