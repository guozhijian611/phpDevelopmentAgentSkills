<?php
use Webman\Route;
Route::get('/labphinx/items', [\plugin\labphinx\app\controller\ItemsController::class, 'index']);
