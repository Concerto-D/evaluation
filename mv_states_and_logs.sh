dir_to_save=$1
mkdir old_experiments_states_and_logs/$dir_to_save/evaluation/
mkdir old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/
mkdir old_experiments_states_and_logs/$dir_to_save/concerto-decentralized/

cp -r experiment/sweeps* old_experiments_states_and_logs/$dir_to_save/evaluation/
cp -r experiment_logs/* old_experiments_states_and_logs/$dir_to_save/evaluation/

cp -r concerto-decentralized-synchrone/concerto/archives_reprises/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/
cp -r concerto-decentralized-synchrone/concerto/reprise_configs/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/
cp -r concerto-decentralized-synchrone/concerto/communication_cache/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/
cp -r concerto-decentralized-synchrone/concerto/finished_reconfigurations/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/
cp -r concerto-decentralized-synchrone/concerto/logs/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized-synchrone/

cp -r concerto-decentralized/concerto/archives_reprises/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized/
cp -r concerto-decentralized/concerto/reprise_configs/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized/
cp -r concerto-decentralized/concerto/finished_reconfigurations/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized/
cp -r concerto-decentralized/concerto/logs/ old_experiments_states_and_logs/$dir_to_save/concerto-decentralized/