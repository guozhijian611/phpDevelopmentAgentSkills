<?php

declare(strict_types=1);
namespace plugin\labpermit\app\middleware;

use plugin\saiadmin\app\cache\ReflectionCache;
use plugin\saiadmin\app\cache\UserAuthCache;
use plugin\saiadmin\exception\ApiException;
use Webman\Http\Request;
use Webman\Http\Response;
use Webman\MiddlewareInterface;
use support\think\Db;

/** Same system permission store as CheckAuth, with mandatory declarations and JSON-safe denial. */
final class RequirePermission implements MiddlewareInterface
{
    public function process(Request $request, callable $handler): Response
    {
        $permission = ReflectionCache::getPermissionAttributes($request->controller, $request->action);
        if (empty($permission['slug'])) throw new ApiException('接口未声明权限，拒绝访问', 403);
        $info = getCurrentInfo();
        $id = (int)($info['id'] ?? 0);
        if (!$id || ($info['plat'] ?? '') !== 'saiadmin' || !Db::table('sa_system_user')->where('id',$id)->where('status',1)->whereNull('delete_time')->count())
            throw new ApiException('登录账号已失效', 401);
        if ($id !== 1 && !in_array($permission['slug'], UserAuthCache::getUserAuth($id), true))
            throw new ApiException('权限不足，无法访问或操作', 403);
        return $handler($request);
    }
}
