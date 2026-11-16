<?php
namespace plugin\labphinx\db\migrations;
use Phinx\Migration\AbstractMigration;
final class CreateLabphinxItems extends AbstractMigration {
 public function up(): void {
  $this->table('labphinx_items')->addColumn('label','string',['limit'=>100])->create();
  $this->table('sa_system_menu')->insert(['parent_id'=>0,'name'=>'Phinx测试','code'=>'LabPhinx','slug'=>'','type'=>2,'path'=>'/labphinx','component'=>'/plugin/labphinx/index','icon'=>'ri:test-tube-line','sort'=>101,'status'=>1,'is_hidden'=>2,'is_keep_alive'=>2,'is_iframe'=>2,'is_fixed_tab'=>2,'is_full_page'=>2])->saveData();
 }
 public function down(): void {
  $this->execute("DELETE FROM sa_system_menu WHERE code = 'LabPhinx'");
  $this->table('labphinx_items')->drop()->save();
 }
}
