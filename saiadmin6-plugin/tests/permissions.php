<?php
/** Offline tests use SQLite only to exercise registry mutations, not to claim MySQL/PG runtime coverage. */
namespace plugin\saiadmin\exception {class ApiException extends \RuntimeException {}}
namespace plugin\saiadmin\app\cache {
    class UserMenuCache {public static function clearMenuCache() {}}
    class UserAuthCache {public static function cacheConfig() {return ['tag'=>'fixture'];}}
    class ReflectionCache {public static function clear() {}}
}
namespace support\think {class Cache {public static function tag($tag) {return new class {public function clear() {}};}}}
namespace {
require __DIR__.'/../assets/permission-fixture/plugin/labpermit/app/service/Permissions.php';
require __DIR__.'/../assets/permission-fixture/plugin/labpermit/app/service/RoleDataScope.php';
require __DIR__.'/../assets/permission-fixture/plugin/labpermit/app/service/MigrationGuard.php';
use plugin\labpermit\app\service\Permissions;
use plugin\labpermit\app\service\RoleDataScope;
function check($ok,$message) {if (!$ok) throw new \RuntimeException($message);}
check(RoleDataScope::role([['id'=>2,'data_scope'=>1],['id'=>3,'data_scope'=>5]])['id']===3,'Numeric scope precedence');
check(RoleDataScope::role([['id'=>4,'data_scope'=>2],['id'=>2,'data_scope'=>2]])['id']===2,'Equal-scope order');
foreach ([[],[['id'=>1,'data_scope'=>0]],[['id'=>1,'data_scope'=>6]]] as $roles) {
    try {RoleDataScope::role($roles);throw new \RuntimeException('Invalid roles accepted');} catch (\plugin\saiadmin\exception\ApiException) {}
}
$db=new \PDO('sqlite::memory:');$db->setAttribute(\PDO::ATTR_ERRMODE,\PDO::ERRMODE_EXCEPTION);
$db->exec('CREATE TABLE sa_system_menu (id INTEGER PRIMARY KEY AUTOINCREMENT,parent_id INTEGER,name TEXT,code TEXT,slug TEXT,type INTEGER,path TEXT,component TEXT,status INTEGER,remark TEXT)');
$db->exec('CREATE TABLE sa_system_role_menu (id INTEGER PRIMARY KEY AUTOINCREMENT,role_id INTEGER,menu_id INTEGER)');
$db->exec("INSERT INTO sa_system_menu (name,code,slug,remark) VALUES ('Shared role data','Shared','core:role:data',NULL)");
$service=new Permissions($db);$service->apply(true);
$old=$db->query("SELECT id FROM sa_system_menu WHERE slug='labpermit:legacy:read'")->fetchColumn();
$db->exec('INSERT INTO sa_system_role_menu (role_id,menu_id) VALUES (22,'.(int)$old.')');
$service->apply();
$point=$db->query("SELECT id FROM sa_system_menu WHERE slug='labpermit:items:stats'")->fetchColumn();
check($db->query('SELECT count(*) FROM sa_system_role_menu WHERE role_id=22 AND menu_id='.(int)$point)->fetchColumn()==1,'Legacy grant not copied');
check($db->query('SELECT count(*) FROM sa_system_role_menu WHERE role_id=99')->fetchColumn()==0,'Unrelated role granted');
$db->exec('DELETE FROM sa_system_role_menu WHERE menu_id='.(int)$point);$snapshot=$db->query('SELECT * FROM sa_system_menu ORDER BY id')->fetchAll();
$service->apply();check($snapshot===$db->query('SELECT * FROM sa_system_menu ORDER BY id')->fetchAll(),'Repeated integration changed IDs');
check($db->query('SELECT count(*) FROM sa_system_role_menu WHERE menu_id='.(int)$point)->fetchColumn()==0,'Revoked grant restored');
$service->remove(true);check($db->query('SELECT count(*) FROM sa_system_role_menu')->fetchColumn()==0,'Owned links left');
check($db->query("SELECT count(*) FROM sa_system_menu WHERE slug='core:role:data'")->fetchColumn()==1,'Shared permission deleted');
$db->exec("INSERT INTO sa_system_menu (name,slug,remark) VALUES ('Collision','labpermit:items:save','another-plugin')");
$before=$db->query('SELECT * FROM sa_system_menu')->fetchAll();
try {$service->apply();throw new \LogicException('Collision accepted');} catch (\RuntimeException $e) {check($e->getMessage()==='Permission slug collision','Unexpected failure');}
check($before===$db->query('SELECT * FROM sa_system_menu')->fetchAll(),'Collision partially changed registry');
$guard=new class($db) {
    use \plugin\labpermit\app\service\MigrationGuard;
    public function __construct(private \PDO $db) {}
    public function getAdapter() {return new class($this->db) {public function __construct(private \PDO $db) {} public function getConnection() {return $this->db;}};}
    public function fail() {$this->guarded(function() {$this->db->beginTransaction();$this->db->exec('DELETE FROM sa_system_menu');throw new \RuntimeException('expected failure');});}
};
try {$guard->fail();} catch (\RuntimeException $e) {check($e->getMessage()==='expected failure','Lost original migration failure');}
check(!$db->inTransaction()&&$before===$db->query('SELECT * FROM sa_system_menu')->fetchAll(),'Migration error leaked transaction or writes');
echo "PASS offline numeric/tie scope policy, invalid roles, natural-key registry, legacy grant mapping, revoked grant persistence and shared-menu preservation\n";
}
