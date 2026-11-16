<?php
/** CLI-only fixture; copied to a disposable server root. Never part of the install ZIP. */
declare(strict_types=1);
namespace plugin\labpermit\app\service {
    function getCurrentInfo(): array|bool { return isset($GLOBALS['fixtureActor']) ? ['id'=>$GLOBALS['fixtureActor']] : \getCurrentInfo(); }
}
namespace {
if (PHP_SAPI!=='cli'||($argv[1]??'')!=='--disposable-fixture') throw new \RuntimeException('CLI disposable fixture flag required');
require getcwd().'/vendor/autoload.php';require getcwd().'/support/bootstrap.php';
use support\think\Db;
use plugin\labpermit\app\service\Permissions;
use plugin\labpermit\app\service\RoleDataScope;
$mode=$argv[2]??'';$file=getcwd().'/runtime/labpermit-fixture.json';
function check(bool $ok,string $message): void { if (!$ok) throw new \RuntimeException($message); }
function clearFixture(): void {
    Permissions::clear();
    foreach ($GLOBALS['state']['users'] ?? [] as $id) \plugin\saiadmin\app\cache\UserInfoCache::clearUserInfo($id);
}
if ($mode==='setup') {
    check(!is_file($file),'Use a new lab for another fixture');
    Db::startTrans();
    try {
        $tag=bin2hex(random_bytes(4));$state=['users'=>[],'roles'=>[],'items'=>[],'tokens'=>[]];
        $a=Db::table('sa_system_dept')->insertGetId(['parent_id'=>0,'name'=>'lp_A_'.$tag,'level'=>'0,','status'=>1]);
        $child=Db::table('sa_system_dept')->insertGetId(['parent_id'=>$a,'name'=>'lp_child_'.$tag,'level'=>'0,'.$a.',','status'=>1]);
        $b=Db::table('sa_system_dept')->insertGetId(['parent_id'=>0,'name'=>'lp_B_'.$tag,'level'=>'0,','status'=>1]);
        $state['departments']=[$a,$child,$b];
        foreach (['actor','creators','menuOnly','none'] as $key) $state['roles'][$key]=Db::table('sa_system_role')->insertGetId(['name'=>'lp_'.$key,'code'=>'lp_'.$tag.'_'.$key,'level'=>10,'data_scope'=>5,'status'=>1]);
        foreach (['actor'=>$a,'peer'=>$a,'child'=>$child,'other'=>$b,'unbound'=>0,'noRole'=>$a,'menuOnly'=>$a,'none'=>$a] as $key=>$dept) {
            $name='lp_'.$tag.'_'.$key;
            $id=Db::table('sa_system_user')->insertGetId(['username'=>$name,'password'=>password_hash(bin2hex(random_bytes(12)),PASSWORD_DEFAULT),'realname'=>$key,'dept_id'=>$dept,'status'=>1]);
            $state['users'][$key]=$id;
            if ($key!=='noRole') Db::table('sa_system_user_role')->insert(['user_id'=>$id,'role_id'=>$state['roles'][in_array($key,['actor','menuOnly','none'],true)?$key:'creators']]);
            $state['tokens'][$key]=\Tinywan\Jwt\JwtToken::generateToken(['id'=>$id,'plat'=>'saiadmin','username'=>$name])['access_token'];
        }
        $menus=Db::table('sa_system_menu')->whereLike('remark','labpermit:%')->select()->toArray();
        foreach (['actor','creators','menuOnly'] as $key) foreach ($menus as $menu) {
            if ($key==='menuOnly'&&(int)$menu['type']===3) continue;
            Db::table('sa_system_role_menu')->insert(['role_id'=>$state['roles'][$key],'menu_id'=>$menu['id']]);
        }
        foreach (['actor','peer','child','other'] as $index=>$key) {
            $id=Db::table('labpermit_items')->insertGetId(['label'=>$key,'amount'=>$index+1,'created_by'=>$state['users'][$key]]);
            $state['items'][$key]=$id;
            Db::table('labpermit_children')->insert(['parent_id'=>$id,'label'=>$key.' child']);
        }
        $state['shared']=['roles'=>Db::table('sa_system_role')->order('id')->select()->toArray(),'departments'=>Db::table('sa_system_dept')->order('id')->select()->toArray(),
            'menus'=>Db::table('sa_system_menu')->where(function($q){$q->whereNull('remark')->whereOr('remark','not like','labpermit:%');})->order('id')->select()->toArray()];
        $state['menu_ids']=array_column($menus,'id');
        Db::commit();file_put_contents($file,json_encode($state,JSON_THROW_ON_ERROR));chmod($file,0600);clearFixture();
    } catch (\Throwable $e) { Db::rollback();throw $e; }
    echo "PASS synthetic fixture ready; credentials remain private\n";exit;
}
$state=json_decode(file_get_contents($file),true,512,JSON_THROW_ON_ERROR);
if ($mode==='custom') {
    Db::table('sa_system_role_dept')->where('role_id',$state['roles']['actor'])->delete();
    if (($argv[3]??'')!=='empty') Db::table('sa_system_role_dept')->insert(['role_id'=>$state['roles']['actor'],'dept_id'=>$state['departments'][2]]);
    clearFixture();
} elseif ($mode==='permission') {
    $slug=$argv[3]??'';check(in_array($slug,array_map(fn($a)=>'labpermit:items:'.$a,array_keys(Permissions::ACTIONS)),true),'Invalid test permission');
    $id=Db::table('sa_system_menu')->where('slug',$slug)->value('id');
    Db::table('sa_system_role_menu')->where(['role_id'=>$state['roles']['actor'],'menu_id'=>$id])->delete();
    clearFixture();(new Permissions(Db::connect()->getPdo()))->apply();
    check(!Db::table('sa_system_role_menu')->where(['role_id'=>$state['roles']['actor'],'menu_id'=>$id])->count(),'Repeat integration regranted a revoked point');
} elseif ($mode==='probe') {
    $adapter=new RoleDataScope();$role=$state['roles']['actor'];
    Db::table('sa_system_role')->where('id',$role)->update(['data_scope'=>5]);
    $GLOBALS['fixtureActor']=$state['users']['actor'];
    check($adapter->apply(Db::table('labpermit_items'))->where('id',$state['items']['actor'])->count()===1,'Self scope mismatch');
    $GLOBALS['fixtureActor']=$state['users']['peer'];
    check(array_map('intval',$adapter->apply(Db::table('labpermit_items'))->column('id'))==[(int)$state['items']['peer']],'Reused scope leaked actor');
    $GLOBALS['fixtureActor']=$state['users']['noRole'];
    try {$adapter->apply(Db::table('labpermit_items'));throw new \RuntimeException('No-role scope allowed');} catch (\plugin\saiadmin\exception\ApiException) {}
    $GLOBALS['fixtureActor']=$state['users']['actor'];Db::table('sa_system_role')->where('id',$role)->update(['data_scope'=>0]);
    try {$adapter->apply(Db::table('labpermit_items'));throw new \RuntimeException('Invalid scope allowed');} catch (\plugin\saiadmin\exception\ApiException) {}
    Db::table('sa_system_role')->where('id',$role)->update(['data_scope'=>5]);
    Db::table('sa_system_role')->where('id',$state['roles']['creators'])->update(['data_scope'=>3]);
    $GLOBALS['fixtureActor']=$state['users']['unbound'];check($adapter->apply(Db::table('labpermit_items'))->count()===0,'Unbound department allowed');
    Db::table('sa_system_role')->where('id',$state['roles']['creators'])->update(['data_scope'=>5]);
    unset($GLOBALS['fixtureActor']);clearFixture();
    echo "PASS real DB reused scope, no role, invalid enum and unbound department\n";
} elseif ($mode==='pgsql') {
    // Probe an owned TEMP table, never overwrite or patch the core role writer.
    Db::execute('CREATE TEMPORARY TABLE labpermit_bigint_probe (role_id bigint, menu_id bigint)');
    // This ORM introspects public schema only; TEMP columns need the actual explicit field types.
    $probe=static fn()=>Db::table('labpermit_bigint_probe')->setFieldType(['role_id'=>'bigint','menu_id'=>'bigint']);
    $data=[['role_id'=>1,'menu_id'=>2],['role_id'=>3,'menu_id'=>4]];$reproduced=false;
    Db::startTrans();
    try {$probe()->insertAll($data);} catch (\Throwable $e) {
        $reproduced=str_contains($e->getMessage(),'42804');check($reproduced,'Unexpected insertAll failure');
    } finally {Db::rollback();}
    // Raw bound VALUES avoids this ORM's TEMP-table auto-increment introspection too.
    Db::transaction(function() use ($data) {foreach ($data as $row) Db::execute('INSERT INTO labpermit_bigint_probe (role_id,menu_id) VALUES (?,?)',[$row['role_id'],$row['menu_id']]);});
    check(Db::table('labpermit_bigint_probe')->count()===2,'VALUES insert failed');
    check((int)Db::query("SELECT count(*) AS n FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction'")[0]['n']===0,'Leaked PostgreSQL transaction');
    echo 'PASS PostgreSQL rollback and VALUES insert; batch 42804 reproduced='.($reproduced?'yes':'no (runtime already supports batch)')."\n";
} elseif ($mode==='cleanup') {
    $ids=Db::table('labpermit_items')->whereIn('created_by',array_values($state['users']))->column('id');
    if ($ids) {Db::table('labpermit_children')->whereIn('parent_id',$ids)->delete();Db::table('labpermit_items')->whereIn('id',$ids)->delete();}
    // Restore the fixture role fields before recording shared-system snapshots for uninstall.
    $state['shared']['roles']=Db::table('sa_system_role')->order('id')->select()->toArray();
    $state['menu_ids']=Db::table('sa_system_menu')->whereLike('remark','labpermit:%')->column('id');
    file_put_contents($file,json_encode($state,JSON_THROW_ON_ERROR));chmod($file,0600);
} elseif ($mode==='uninstalled') {
    $schema=getenv('DB_TYPE')==='pgsql' ? 'current_schema()' : 'DATABASE()';
    check(!Db::query("SELECT table_name FROM information_schema.tables WHERE table_schema = ".$schema." AND table_name IN ('labpermit_items','labpermit_children','phinxlog_labpermit')"),'Owned schema or migration log leaked');
    check(!Db::table('sa_system_menu')->whereLike('remark','labpermit:%')->count(),'Owned menu leaked');
    check(!Db::table('sa_system_role_menu')->whereIn('menu_id',$state['menu_ids'])->count(),'Owned role-menu links leaked');
    check(Db::table('sa_system_role')->order('id')->select()->toArray()===$state['shared']['roles'],'System roles changed');
    check(Db::table('sa_system_dept')->order('id')->select()->toArray()===$state['shared']['departments'],'System departments changed');
    $menus=Db::table('sa_system_menu')->where(function($q){$q->whereNull('remark')->whereOr('remark','not like','labpermit:%');})->order('id')->select()->toArray();
    check($menus===$state['shared']['menus'],'Shared system menus changed');
    echo "PASS uninstall preserves roles, departments and shared menus\n";
} else throw new \RuntimeException('Unknown fixture command');
}
