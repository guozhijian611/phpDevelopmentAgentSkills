<?php
namespace plugin\labphinx\db\seeds;
use Phinx\Seed\AbstractSeed;
final class LabPhinxSeeder extends AbstractSeed {
 public function run(): void {$this->table('labphinx_items')->insert(['label'=>'seed-once'])->saveData();}
}
