<?php
declare(strict_types=1);
namespace plugin\labpermit\app\service;

use PDO;

/** Backend-only disposable example: stable natural keys; VALUES inserts on both databases. */
final class Permissions
{
    public const LEGACY = ['read'=>'Read records','write'=>'Write records'];
    public const ACTIONS = ['index'=>'read','read'=>'read','stats'=>'read','children'=>'read','save'=>'write','update'=>'write','destroy'=>'write'];
    public function __construct(private readonly PDO $db) {}

    public function apply(bool $legacy = false): void
    {
        $this->preflight($legacy);
        $root = $this->one('SELECT * FROM sa_system_menu WHERE code = ?', ['LabPermit']);
        $items = $legacy ? self::LEGACY : self::ACTIONS;
        $own = !$this->db->inTransaction();
        if ($own) $this->db->beginTransaction();
        try {
            if (!$root) {
                $this->run('INSERT INTO sa_system_menu (parent_id,name,code,slug,type,path,component,status,remark) VALUES (0,?,?,?,?,?,?,1,?)',
                    ['Permission fixture','LabPermit','',1,'/labpermit','/index/index','labpermit:root']);
                $root = $this->one('SELECT * FROM sa_system_menu WHERE code = ?', ['LabPermit']);
            }
            foreach ($items as $action=>$value) {
                $slug = 'labpermit:'.($legacy ? 'legacy:' : 'items:').$action;
                if ($this->one('SELECT id FROM sa_system_menu WHERE slug = ?', [$slug])) continue;
                $this->run('INSERT INTO sa_system_menu (parent_id,name,slug,type,status,remark) VALUES (?,?,?,3,1,?)',
                    [$root['id'],$legacy ? $value : ucfirst($action).' records',$slug,$legacy ? 'labpermit:legacy' : 'labpermit:actions']);
                $node = $this->one('SELECT id FROM sa_system_menu WHERE slug = ?', [$slug]);
                if (!$legacy) {
                    $old = $this->one('SELECT id FROM sa_system_menu WHERE slug = ?', ['labpermit:legacy:'.$value]);
                    if ($old) foreach ($this->run('SELECT role_id FROM sa_system_role_menu WHERE menu_id = ?', [$old['id']])->fetchAll(PDO::FETCH_COLUMN) as $role) {
                        $this->run('INSERT INTO sa_system_role_menu (role_id,menu_id) VALUES (?,?)', [$role,$node['id']]);
                    }
                }
            }
            if ($own) $this->db->commit();
            self::clear();
        } catch (\Throwable $e) {
            if ($own && $this->db->inTransaction()) $this->db->rollBack();
            throw $e;
        }
    }

    /** May run before MySQL DDL, which cannot be rolled back with the permission rows. */
    public function preflight(bool $legacy = false): void
    {
        $root=$this->one('SELECT * FROM sa_system_menu WHERE code = ?', ['LabPermit']);
        if ($root && $root['remark']!=='labpermit:root') throw new \RuntimeException('Menu code collision');
        foreach (($legacy ? self::LEGACY : self::ACTIONS) as $action=>$value) {
            $slug='labpermit:'.($legacy ? 'legacy:' : 'items:').$action;
            $existing=$this->one('SELECT * FROM sa_system_menu WHERE slug = ?', [$slug]);
            if ($existing && $existing['remark']!==($legacy ? 'labpermit:legacy' : 'labpermit:actions')) throw new \RuntimeException('Permission slug collision');
        }
    }

    public function remove(bool $all = false): void
    {
        $marks = $all ? ['labpermit:root','labpermit:legacy','labpermit:actions'] : ['labpermit:actions'];
        foreach ($marks as $mark) {
            foreach ($this->run('SELECT id FROM sa_system_menu WHERE remark = ?', [$mark])->fetchAll(PDO::FETCH_COLUMN) as $id)
                $this->run('DELETE FROM sa_system_role_menu WHERE menu_id = ?', [$id]);
            $this->run('DELETE FROM sa_system_menu WHERE remark = ?', [$mark]);
        }
        self::clear();
    }

    public static function clear(): void
    {
        \plugin\saiadmin\app\cache\UserMenuCache::clearMenuCache();
        \support\think\Cache::tag(\plugin\saiadmin\app\cache\UserAuthCache::cacheConfig()['tag'])->clear();
        \plugin\saiadmin\app\cache\ReflectionCache::clear();
    }

    private function one(string $sql, array $args): ?array
    {
        $rows=$this->run($sql,$args)->fetchAll(PDO::FETCH_ASSOC);
        if (count($rows)>1) throw new \RuntimeException('Duplicate natural key');
        return $rows[0] ?? null;
    }
    private function run(string $sql, array $args): \PDOStatement
    {
        $s=$this->db->prepare($sql);$s->execute($args);return $s;
    }
}
