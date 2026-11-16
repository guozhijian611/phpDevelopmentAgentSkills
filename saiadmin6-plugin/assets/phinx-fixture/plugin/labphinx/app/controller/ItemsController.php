<?php
namespace plugin\labphinx\app\controller;
class ItemsController extends \plugin\saiadmin\basic\BaseController {
 public function index() {return $this->success(\support\Db::table('labphinx_items')->orderBy('id')->get()->toArray());}
}
