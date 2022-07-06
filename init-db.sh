psql postgres -c "revoke connect on database efficiensee from public;"
psql postgres -c "SELECT
                    pg_terminate_backend(pid)
                  FROM
                    pg_stat_activity
                  WHERE
                    pid <> pg_backend_pid()
                    AND datname = 'efficiensee'
                  ;"
psql postgres -c "drop database if exists efficiensee;"
psql postgres -c "drop role if exists efficiensee;"
psql postgres -c "create database efficiensee;"
psql postgres -c "grant connect on database efficiensee to public;"

psql efficiensee -c "create role efficiensee;"
psql efficiensee -c "alter role efficiensee with login;"
psql efficiensee -c "alter role efficiensee with password 'efficiensee';"
psql efficiensee -c "grant all privileges on database efficiensee to efficiensee;"
psql efficiensee -c "alter role efficiensee superuser;"

psql efficiensee -c "alter role efficiensee set client_encoding to 'utf8'"
psql efficiensee -c "alter role efficiensee set timezone to 'UTC'"
# fixme
