<?php
use Webman\Route;
use plugin\labpermit\app\controller\ItemsController as C;
foreach (['index','read','stats','children'] as $action) Route::get('/app/labpermit/items/'.$action,[C::class,$action]);
Route::post('/app/labpermit/items/save',[C::class,'save']);
Route::put('/app/labpermit/items/update',[C::class,'update']);
Route::delete('/app/labpermit/items/destroy',[C::class,'destroy']);
