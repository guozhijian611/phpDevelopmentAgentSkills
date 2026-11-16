<?php
namespace plugin\labpermit\db\migrations;
use Phinx\Migration\AbstractMigration;
use plugin\labpermit\app\service\Permissions;
final class CreateLabpermit extends AbstractMigration
{
    use \plugin\labpermit\app\service\MigrationGuard;
    public function up(): void {
      $this->guarded(function () {
        foreach (['sa_system_user','sa_system_role','sa_system_user_role','sa_system_dept','sa_system_role_dept','sa_system_menu','sa_system_role_menu'] as $name)
            if (!$this->hasTable($name)) throw new \RuntimeException('Missing system permission table: '.$name);
        if (!$this->table('sa_system_role')->hasColumn('data_scope')) throw new \RuntimeException('Missing role scope');
        (new Permissions($this->getAdapter()->getConnection()))->preflight(true);
        $this->table('labpermit_items')->addColumn('label','string',['limit'=>80])->addColumn('amount','integer',['default'=>1])
            ->addColumn('created_by','biginteger')->addIndex(['created_by'],['name'=>'labpermit_owner'])->create();
        $this->table('labpermit_children')->addColumn('parent_id','biginteger')->addColumn('label','string',['limit'=>80])->create();
        (new Permissions($this->getAdapter()->getConnection()))->apply(true);
      });
    }
    public function down(): void {
      $this->guarded(function () {
        foreach (['labpermit_items','labpermit_children'] as $name)
            if ($this->hasTable($name)&&(int)$this->fetchRow('SELECT COUNT(*) AS n FROM '.$name)['n']) throw new \RuntimeException('Fixture data must be explicitly cleared first');
        (new Permissions($this->getAdapter()->getConnection()))->remove(true);
        $this->table('labpermit_children')->drop()->save();$this->table('labpermit_items')->drop()->save();
      });
    }
}
