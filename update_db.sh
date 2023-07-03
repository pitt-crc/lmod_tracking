sed "s|lmod.log|$log_path|g" $1 | mysql --defaults-file=db.cnf -vvv

