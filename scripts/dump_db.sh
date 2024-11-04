DBNAME='alyx_db'
DBUSER='tjostmou'
FILENAME='alyx.sql'

pg_dump -cOx -U $DBUSER -h localhost $DBNAME -f $FILENAME
gzip $FILENAME


