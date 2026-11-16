#!/usr/bin/env python3
"""Offline CLI regression using a disposable host adapter; never accesses a real database."""
from pathlib import Path
import json, os, subprocess, tempfile, unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'saicode_generate.php'
PHP_FIXTURE = r'''<?php
namespace fixture {
class Row { public function __isset($n){return isset($this->toArray()[$n]);} public function __get($n){return $this->toArray()[$n]??null;} public function isEmpty(){return false;} public function toArray(){return json_decode(file_get_contents(\base_path().'/row.json'),true);} }
class Rows { function __construct(private array $rows){} function toArray(){return $this->rows;} }
}
namespace plugin\saicode\app\model { class Table { static function findOrEmpty($id){return new \fixture\Row;} } class Column {} }
namespace support\think {
class Query {
 private array $conditions=[];
 function where($field,$value){$this->conditions[$field]=$value;return $this;}
 function whereIn($field,$value){$this->conditions[$field]=$value;return $this;}
 private function matches($row){foreach($this->conditions as $k=>$v){if(is_array($v)?!in_array($row[$k],$v):$row[$k]!=$v)return false;}return true;}
 function select(){return new \fixture\Rows(array_values(array_filter(Db::rows(),fn($r)=>$this->matches($r))));}
 function delete(){if(is_file(\base_path().'/fail-db'))throw new \RuntimeException('injected database failure');Db::save(array_values(array_filter(Db::rows(),fn($r)=>!$this->matches($r))));}
}
class Db {
 static function rows(){return json_decode(file_get_contents(\base_path().'/menus.json'),true);}
 static function save($rows){file_put_contents(\base_path().'/menus.json',json_encode($rows));}
 static function table($name){return new Query;}
 static function transaction($fn){$before=self::rows();try{$fn();}catch(\Throwable $e){self::save($before);throw $e;}}
}
}
namespace plugin\saicode\app\logic {
class DbLogic {}
class TableLogic {
 function generateFile($id){$row=(new \fixture\Row)->toArray();$ledger=new \GenerationLedger(\base_path(),$id,$row);foreach($ledger->targets() as $p){if(!is_dir(dirname($p)))mkdir(dirname($p),0777,true);file_put_contents($p,'generated fixture '.$p);} \support\think\Db::save([['id'=>11,'parent_id'=>0,'generate_id'=>$id,'name'=>'Generated'],['id'=>12,'parent_id'=>11,'generate_id'=>0,'name'=>'Read']]);}
}
}
'''

class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='saicode CLI 中文 ')
        self.root=Path(self.temp.name);self.server=self.root/'backend';self.front=self.root/'admin-ui'
        for p in ['vendor','support','plugin/saicode']:(self.server/p).mkdir(parents=True,exist_ok=True)
        self.front.mkdir()
        (self.server/'vendor/autoload.php').write_text(PHP_FIXTURE)
        (self.server/'support/bootstrap.php').write_text('<?php function base_path(){return dirname(__DIR__);}')
        self.row={'namespace':'demo','class_name':'Item','business_name':'items','generate_path':'admin-ui','template':'plugin','package_name':'system'}
        self.save_row();(self.server/'menus.json').write_text('[]')
        self.env=dict(os.environ);self.env.pop('SERVER_DIR',None)
    def tearDown(self):self.temp.cleanup()
    def save_row(self):(self.server/'row.json').write_text(json.dumps(self.row))
    def run_cli(self,*args,ok=True,host=True):
        argv=['php',str(CLI),*args]
        if host:argv+=['--server-dir',str(self.server)]
        r=subprocess.run(argv,cwd=self.root,env=self.env,capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode==0,ok,r.stdout+r.stderr);return r
    def ledger(self):return self.server/'runtime/saicode-skill/1.json'
    def test_help_and_explicit_path_errors(self):
        self.run_cli('--help',host=False);self.run_cli('-h',host=False)
        self.run_cli('unknown',ok=False,host=False)
        self.run_cli('generate','--server-dir=/missing','--id=1',ok=False,host=False)
        self.run_cli('generate','--id',ok=False,host=False)
        self.assertFalse((self.server/'runtime').exists())
    def test_cwd_detection_and_dry_run(self):
        self.run_cli('generate','--id=1','--dry-run')
        self.assertFalse(self.ledger().exists());self.assertEqual((self.server/'menus.json').read_text(),'[]')
        r=subprocess.run(['php',str(CLI),'generate','--id','1','--dry-run'],cwd=self.server,env=self.env,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
    def test_generation_edits_guard_and_transaction_recovery(self):
        self.run_cli('generate','--id','1');record=json.loads(self.ledger().read_text())
        paths=[Path(p) for p in record['files']];contents={p:p.read_bytes() for p in paths};menus=(self.server/'menus.json').read_bytes()
        user=self.server/'plugin/demo/user.txt';user.write_text('user owned')
        self.run_cli('rollback','--id=1');self.assertTrue(all(p.exists() for p in paths))
        paths[0].write_text('later user edit')
        self.run_cli('rollback','--id=1','--apply',ok=False);self.run_cli('generate','--id=1',ok=False)
        self.assertTrue(all(p.exists() for p in paths));self.assertEqual((self.server/'menus.json').read_bytes(),menus)
        paths[0].write_bytes(contents[paths[0]])
        data=json.loads(menus);data[0]['name']='user menu edit';(self.server/'menus.json').write_text(json.dumps(data))
        self.run_cli('rollback','--id=1','--apply',ok=False);self.assertTrue(all(p.exists() for p in paths))
        self.run_cli('generate','--id=1',ok=False)
        (self.server/'menus.json').write_bytes(menus);(self.server/'fail-db').touch()
        self.run_cli('rollback','--id=1','--apply',ok=False)
        self.assertTrue(all(p.read_bytes()==contents[p] for p in paths));self.assertTrue(self.ledger().exists())
        (self.server/'fail-db').unlink();self.run_cli('rollback','--id=1','--apply')
        self.assertTrue(all(not p.exists() for p in paths));self.assertEqual(user.read_text(),'user owned');self.assertFalse(self.ledger().exists())
        self.assertEqual(json.loads((self.server/'menus.json').read_text()),[])
    def test_repeat_generation_and_changed_configuration(self):
        self.run_cli('generate','--id=1');before=self.ledger().read_bytes()
        self.run_cli('generate','--id=1');self.assertEqual(self.ledger().read_bytes(),before)
        self.row['business_name']='different';self.save_row()
        self.run_cli('rollback','--id=1','--apply',ok=False);self.assertEqual(self.ledger().read_bytes(),before)
    def test_unowned_menus_are_not_taken_over(self):
        menus=[{'id':11,'parent_id':0,'generate_id':1,'name':'Existing user menu'}]
        (self.server/'menus.json').write_text(json.dumps(menus))
        self.run_cli('generate','--id=1',ok=False)
        self.assertEqual(json.loads((self.server/'menus.json').read_text()),menus)
        self.assertFalse(self.ledger().exists())
    def test_core_paths_unowned_files_and_symlinks(self):
        for field,value in [('namespace','saiadmin'),('generate_path','../escape'),('package_name','../escape')]:
            before=self.row.copy();self.row[field]=value;self.save_row();self.run_cli('generate','--id=1',ok=False);self.row=before
        self.save_row();target=self.server/'plugin/demo/app/admin/controller/system/ItemController.php';target.parent.mkdir(parents=True);target.write_text('existing user code')
        self.run_cli('generate','--id=1',ok=False);self.assertEqual(target.read_text(),'existing user code')
        target.unlink();outside=self.root/'outside';outside.write_text('outside');target.symlink_to(outside)
        self.run_cli('generate','--id=1',ok=False);self.assertEqual(outside.read_text(),'outside')
        self.run_cli('rollback','--id=1','--apply',ok=False)

if __name__=='__main__':unittest.main()
