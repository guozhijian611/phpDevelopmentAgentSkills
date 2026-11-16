<?php
declare(strict_types=1);
namespace plugin\labpermit\app\controller;

use plugin\labpermit\app\service\RoleDataScope;
use plugin\saiadmin\exception\ApiException;
use plugin\saiadmin\service\Permission;
use support\think\Db;
use support\Request;

final class ItemsController extends \plugin\saiadmin\basic\BaseController
{
    private function scoped(): mixed { return (new RoleDataScope())->apply(Db::table('labpermit_items')); }
    private function record(int $id, bool $lock=false): array
    {
        $row=$this->scoped()->lock($lock)->find($id);
        if (!$row) throw new ApiException('Record unavailable',403);
        return $row;
    }
    #[Permission('List records','labpermit:items:index')]
    public function index(Request $r) {
        $q=$this->scoped();$name=(string)$r->get('name','');
        if ($name!=='') $q->whereLike('label','%'.$name.'%');
        $count=(clone $q)->count();$limit=max(1,min(100,(int)$r->get('limit',100)));
        return $this->success(['total'=>$count,'items'=>$q->order('id')->limit($limit)->select()->toArray()]);
    }
    #[Permission('Read record','labpermit:items:read')]
    public function read(Request $r) { return $this->success($this->record((int)$r->get('id'))); }
    #[Permission('Aggregate records','labpermit:items:stats')]
    public function stats() { return $this->success(['count'=>$this->scoped()->count(),'sum'=>$this->scoped()->sum('amount')]); }
    #[Permission('Read child records','labpermit:items:children')]
    public function children(Request $r) {
        $row=$this->record((int)$r->get('id'));
        return $this->success(Db::table('labpermit_children')->where('parent_id',$row['id'])->select()->toArray());
    }
    #[Permission('Create record','labpermit:items:save')]
    public function save(Request $r) {
        $this->scoped(); // Reject an invalid actor/role even though no existing row is read.
        $label=trim((string)$r->post('label',''));
        if ($label===''||strlen($label)>80) throw new ApiException('Invalid label');
        $id=Db::table('labpermit_items')->insertGetId(['label'=>$label,'amount'=>1,'created_by'=>RoleDataScope::actor()]);
        return $this->success(['id'=>$id]);
    }
    #[Permission('Update record','labpermit:items:update')]
    public function update(Request $r) {
        Db::transaction(function() use ($r) {
            $row=$this->record((int)$r->input('id'),true);
            $label=trim((string)$r->input('label',''));
            if ($label===''||strlen($label)>80) throw new ApiException('Invalid label');
            // Only an explicit writable field is accepted; no owner, amount or parent reassignment.
            $this->scoped()->where('id',$row['id'])->update(['label'=>$label]);
        });
        return $this->success();
    }
    #[Permission('Delete records','labpermit:items:destroy')]
    public function destroy(Request $r) {
        $ids=$r->input('ids',[]);
        if (!is_array($ids)||!$ids||count($ids)>100) throw new ApiException('Invalid selection');
        $ids=array_unique(array_map('intval',$ids));
        Db::transaction(function() use ($ids) {
            foreach ($ids as $id) $this->record($id,true);
            foreach ($ids as $id) { Db::table('labpermit_children')->where('parent_id',$id)->delete();$this->scoped()->where('id',$id)->delete(); }
        });
        return $this->success();
    }
}
