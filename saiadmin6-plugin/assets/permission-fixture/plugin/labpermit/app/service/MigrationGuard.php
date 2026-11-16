<?php
namespace plugin\labpermit\app\service;
/** Failed Phinx operations must not leave the shared PostgreSQL connection in a transaction. */
trait MigrationGuard
{
    private function guarded(callable $action): void
    {
        try {$action();} catch (\Throwable $error) {
            $connection=$this->getAdapter()->getConnection();
            if ($connection->inTransaction()) $connection->rollBack();
            throw $error;
        }
    }
}
