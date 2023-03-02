set -e  # Exit program on error

# $1: g5k site
# $2: src_dir
# $3: dst_dir

if [[ -z "$3" ]]; then
  echo "need args"
  exit
fi
echo 1
ssh anomond@$1.g5k "cd experiments_results; tar -cf experiments_results.tar $2"
echo 2
scp anomond@$1.g5k:"experiments_results/experiments_results.tar" "/home/aomond/experiments_results"
echo 3
tar --exclude=.ipynb_checkpoints -C "/home/aomond/experiments_results/$3" -xvf "/home/aomond/experiments_results/experiments_results.tar"
echo 4
rm "/home/aomond/experiments_results/experiments_results.tar"
echo 5
#ssh anomond@$1.g5k 'rm -rf experiments_results/*'
