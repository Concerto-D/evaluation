set -e  # Exit program on error

if [[ -z "$1" ]]; then
  echo "need args"
  exit
fi

ssh anomond@nancy.grid5000.fr 'cd experiments_results/; tar -cf experiments_results.tar *'
scp anomond@nancy.grid5000.fr:experiments_results/experiments_results.tar "/home/aomond/experiments_results/"
tar --exclude=.ipynb_checkpoints -C "/home/aomond/experiments_results/$1" -xvf "/home/aomond/experiments_results/experiments_results.tar"
rm "/home/aomond/experiments_results/experiments_results.tar"
ssh anomond@nancy.grid5000.fr 'rm -rf experiments_results/*'
