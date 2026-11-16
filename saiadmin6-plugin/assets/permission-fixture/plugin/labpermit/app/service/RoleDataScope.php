<?php

declare(strict_types=1);
namespace plugin\labpermit\app\service;

use plugin\saiadmin\exception\ApiException;
use support\think\Db;

/** Plugin-local adapter for the supplied SaiAdmin 6 DataScope contract; no core overlay. */
final class RoleDataScope
{
    public static function actor(): int
    {
        $id = (int) (getCurrentInfo()['id'] ?? 0);
        if ($id <= 0) throw new ApiException('请先登录', 401);
        return $id;
    }

    /** Match the official numeric precedence, with deterministic equal-scope role selection. */
    public static function role(array $roles): array
    {
        if (!$roles) throw new ApiException('未配置有效角色，无法访问数据', 403);
        usort($roles, static fn(array $a, array $b): int => (int)$a['id'] <=> (int)$b['id']);
        $selected = null;
        foreach ($roles as $role) {
            $scope = (int) ($role['data_scope'] ?? 0);
            if ($scope < 1 || $scope > 5) throw new ApiException('角色数据范围配置无效', 403);
            if ($selected === null || $scope > (int)$selected['data_scope']) $selected = $role;
        }
        return $selected;
    }

    public function apply($query, string $field = 'created_by'): mixed
    {
        if (!preg_match('/^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)?$/i', $field)) throw new \InvalidArgumentException('Invalid scope field');
        $id = self::actor();
        // Read authoritative scope inputs each time, including for reused Logic instances.
        $user = Db::table('sa_system_user')->where('id', $id)->where('status', 1)->whereNull('delete_time')->find();
        if (!$user) throw new ApiException('登录账号已失效', 401);
        if ($id === 1) return $query; // Same server-side superadmin identity as CheckAuth.
        $roles = Db::table('sa_system_role')->whereIn('id', Db::table('sa_system_user_role')->where('user_id', $id)->column('role_id'))
            ->where('status', 1)->whereNull('delete_time')->field('id,data_scope')->select()->toArray();
        $role = self::role($roles);
        $scope = (int)$role['data_scope'];
        if ($scope === 1) return $query;
        if ($scope === 5) return $query->where($field, $id);
        $departments = Db::table('sa_system_dept')->where('status', 1)->whereNull('delete_time')->field('id,parent_id')->select()->toArray();
        $valid = array_map('intval', array_column($departments, 'id'));
        if ($scope === 2) {
            $ids = array_map('intval', Db::table('sa_system_role_dept')->where('role_id', (int)$role['id'])->column('dept_id'));
            $ids = array_values(array_intersect($ids, $valid));
        } else {
            $department = (int)($user['dept_id'] ?? 0);
            $ids = in_array($department, $valid, true) ? [$department] : [];
            if ($scope === 4 && $ids) {
                // Parent links avoid LIKE-prefix mistakes; visited IDs bound malformed cycles.
                $children = [];
                foreach ($departments as $item) $children[(int)$item['parent_id']][] = (int)$item['id'];
                $visited = [$department => true];
                for ($i = 0; $i < count($ids); $i++) {
                    foreach ($children[$ids[$i]] ?? [] as $child) {
                        if (!isset($visited[$child])) { $ids[] = $child; $visited[$child] = true; }
                    }
                }
            }
        }
        if (!$ids) return $query->whereRaw('1 = 0');
        return $query->whereIn($field, static function ($users) use ($ids) {
            $users->table('sa_system_user')->whereIn('dept_id', $ids)->whereNull('delete_time')->field('id');
        });
    }
}
