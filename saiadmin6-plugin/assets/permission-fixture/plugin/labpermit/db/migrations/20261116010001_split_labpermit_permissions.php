<?php
namespace plugin\labpermit\db\migrations;
use Phinx\Migration\AbstractMigration;
use plugin\labpermit\app\service\Permissions;
final class SplitLabpermitPermissions extends AbstractMigration
{
    use \plugin\labpermit\app\service\MigrationGuard;
    public function up(): void { $this->guarded(function () {(new Permissions($this->getAdapter()->getConnection()))->apply();}); }
    public function down(): void {
      $this->guarded(function () {
        foreach (['labpermit_items','labpermit_children'] as $name)
            if ((int)$this->fetchRow('SELECT COUNT(*) AS n FROM '.$name)['n']) throw new \RuntimeException('Fixture data must be explicitly cleared first');
        (new Permissions($this->getAdapter()->getConnection()))->remove();
      });
    }
}
