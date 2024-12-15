
Generate the available options for each command:

```
python get_rid_of_dup.py search -h   | cut -d ' ' -f 3 | sort | uniq | grep "^--" > search.cmd
python get_rid_of_dup.py checksum -h | cut -d ' ' -f 3 | sort | uniq | grep "^--" > checksum.cmd
python get_rid_of_dup.py delete -h   | cut -d ' ' -f 3 | sort | uniq | grep "^--" > delete.cmd
python get_rid_of_dup.py dedup -h    | cut -d ' ' -f 3 | sort | uniq | grep "^--" > dedup.cmd
```
