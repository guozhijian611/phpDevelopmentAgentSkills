<?php
namespace plugin\labphinx\db\migrations;
use Phinx\Migration\AbstractMigration;
final class AddLabphinxNote extends AbstractMigration {
 public function change(): void {$this->table('labphinx_items')->addColumn('note','string',['null'=>true])->update();}
}
