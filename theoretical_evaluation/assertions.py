import json
from typing import List
import os

import yaml

class AssertionsSynchronous:
    class perc_100:
        class T0:
            @staticmethod
            def assert_synchronous_100_perc_T0_deploy(global_results):
                #     = t_sc_1 + t_di_1 + t_sr
                #     = 34.59
                res = (14.07 + 19.12) + 1.4
                _compute_result()
                delta = abs(global_results["max_deploy_time"] - res)
                delta_perc = delta*100/res
                print(f"assert_synchronous_100_perc_T0_deploy - delta: {delta}s - {delta_perc}%")


            @staticmethod
            def assert_synchronous_100_perc_T0_deploy_sync(global_results):
                # res = max_deploy_duration (server) - overflow_sleeping (server) - min_deploy_duration (dep5)
                #     = 28.6
                res = 34.59 - 3.19 - 2.8
                delta = abs(global_results["max_deploy_time"] - res)
                delta_perc = delta*100/res
                print(f"assert_synchronous_100_perc_T0_deploy_sync - delta: {delta}s - {delta_perc}%")


            @staticmethod
            def assert_synchronous_100_perc_T0_update(global_results):
                # res = max(t_ss_i + max(t_du_i + t_sp_i) + max(t_dr_i, t_sr)) + t_sr
                #     = 20.55
                res = 1.07 + 13.8 + 4.28 + 1.4
                return

            # zip(t_ss, t_sp, t_dus, t_drs)

            @staticmethod
            def assert_synchronous_100_perc_T0_update_sync(global_results):
                # res = max_update_duration (server) - overflow_sleeping (server) - min_update_duration (dep8)
                #     = 17.13
                res = 19.48 - 0 - 2.35
                return

        # Sleeping: 30
        # Sleeping sync: 34

        class T1:
            @staticmethod
            def assert_synchronous_100_perc_T1_deploy(global_results):
                #     = t_sc_3 + t_di_3 + t_sr
                #     = 26.66
                res = 9.82 + 6.33 + 10.51
                return


            @staticmethod
            def assert_synchronous_100_perc_T1_deploy_sync(global_results):
                #     = 22.26
                res = 26.66 - 0 - 2.4
                return


            @staticmethod
            def assert_synchronous_100_perc_T1_update(global_results):
                #     = 35.32  # TODO: calcul à revoir
                res = max_update_duration_100_T1  # TODO: calcul à revoir
                return

            # zip(t_ss, t_sp, t_dus, t_drs)

            @staticmethod
            def assert_synchronous_100_perc_T1_update_sync(global_results):
                #     = 33.55
                res = 38.17 - 0 - 4.62
                return

            # Sleeping: 35
            # Sleeping sync: 35


transitions_times_0 = json.load(open("../parameters/transitions_times/transitions_times-1-30-deps12-0.json"))["transitions_times"]
transitions_times_1 = json.load(open("../parameters/transitions_times/transitions_times-1-30-deps12-1.json"))["transitions_times"]


t_sa_0 = transitions_times_0["server"]["t_sa"]
t_sc_0 = transitions_times_0["server"]["t_sc"]
t_sr_0 = transitions_times_0["server"]["t_sr"]
t_ss_0 = transitions_times_0["server"]["t_ss"]
t_sp_0 = transitions_times_0["server"]["t_sp"]

t_sa_1 = transitions_times_1["server"]["t_sa"]
t_sc_1 = transitions_times_1["server"]["t_sc"]
t_sr_1 = transitions_times_1["server"]["t_sr"]
t_ss_1 = transitions_times_1["server"]["t_ss"]
t_sp_1 = transitions_times_1["server"]["t_sp"]

t_dis_1 = [k["t_di"] for n, k in transitions_times_1.items() if n != "server"]
t_drs_1 = [k["t_dr"] for n, k in transitions_times_1.items() if n != "server"]
t_dus_1 = [k["t_du"] for n, k in transitions_times_1.items() if n != "server"]

# max_du_dr = max([t_dus_1[i] + t_drs_1[i] for i in range(12)])
# max_update_duration_100_T1 = max([t_ss_1[i] + max(t_sp_1[i], max_du_dr) + t_sr_1 for i in range(12)])   OLD
# Au moment où la place s1, s2, etc est quittée, le use port rattaché à cette place est desactivé
max_update_duration_100_T1 = max([(t_ss_1[i] + max(t_sp_1[i], t_dus_1[i] + t_drs_1[i]) + t_sr_1, i) for i in range(12)], key=lambda x: x[0])
min_update_duration_100_T1 = min([t_ss_1[i] + t_dus_1[i] + t_drs_1[i] for i in range(12)])
max_waitall_True_duration = max([t_ss_1[i] + t_dus_1[i] + t_drs_1[i] for i in range(12)])
print(max_update_duration_100_T1)
# print(max_waitall_True_duration)
#
# for i in range(12):
#     print(i, t_ss_1[i] + t_dus_1[i] + t_drs_1[i])


# for i in range(12):
#     print(t_ss_1[i] + max(t_sp_1[i], t_dus_1[i] + t_drs_1[i]))

def _compute_result(func_name, experiment_value, theoretical_value):
    delta = experiment_value - theoretical_value
    delta_perc = delta*100/theoretical_value
    print(f"delta: {round(delta, 2)}s, {round(delta_perc, 2)}%    (expe_val: {experiment_value}, theoric_val: {theoretical_value}) - {func_name}")


# max_deploy_duration      = max(max(t_sa, t_di) + t_sc_i) + t_sr
# min_deploy_duration      = min(t_di + t_dr)
# max_deploy_sync_duration = max_deploy_duration - overflow - min_deploy_duration
# max_update_duration      = max(t_ss_i + max(t_sp_i, max(t_du_j + t_dr_j)) + t_sr)
# min_update_duration      = min(t_ss_i + t_du_i + t_dr_i)
# max_update_sync_duration = max_update_duration - overflow - min_update_duration
theoretical_values = {
    "synchronous": {
        "100": {
            "T0": {
                "max_deploy_time": 34.59,
                "max_deploy_sync_time": 28.6,
                "max_update_time": 20.55,
                "max_update_sync_time": 17.13,
            },
            "T1": {
                "max_deploy_time": 24.81,
                "max_deploy_sync_time": 22.26,
                "max_update_time": 35.32,
                "max_update_sync_time": 24.81,
            },
        },
        "50": {
            "T0": {
                "max_deploy_time": 271.52,    # 9 rounds: 4 rounds conns, 2 rounds 1er sync, 4 rounds 2eme sync + t_sr,
                "max_update_time": 45,        # 2-3 rounds max (1 pour faire toutes les transitions + quelques connections, 1 autre pour le reste des connections + le temps des transitions donc entre 10 et 30 selon les temps de transitions)
            },
            "T1": {
                "max_deploy_time": 280.51,    # 4 rounds conns, 2 rounds 1er sync, 4 rounds 2eme sync + t_sr,
                "max_update_time": 45,        # 2-3 rounds max (1 pour faire toutes les transitions + quelques connections, 1 autre pour le reste des connections + le temps des transitions donc entre 10 et 30 selon les temps de transitions)
            },
        }
    },
    "central": {
        "50-60": {
            "T0": {
                "max_deploy_time": 50.21,      # server: overlap right (21.17 sec added) + t_di (3.96) + t_sc3 (23.88) + t_sr (1.2)
                "max_update_time": 56.56       # server: one whole awaken (30) + time to update and deploy dep9 (2.26 + 1.98) + timeoverlap (24.2) - executionstarttime (~1.9)
            }
        }
    }
}


def print_duration_delta(results_files: List[str]):
    experiments_results_dir = f"{os.getenv('HOME')}/experiments_results"
    for file_name in results_files:
        res = yaml.safe_load(open(f"{experiments_results_dir}/{file_name}"))
        global_results = res["global_results"]
        global_results_sync = res["global_synchronization_results"]

        # if "T0" in file_name:
        #     _compute_result("assert_synchronous_100_perc_T0_deploy", global_results["max_deploy_time"], theoretical_values["synchronous"]["100"]["T0"]["max_deploy_time"])
        #     _compute_result("assert_synchronous_100_perc_T0_deploy_sync", global_results_sync["max_deploy_sync_time"], theoretical_values["synchronous"]["100"]["T0"]["max_deploy_sync_time"])
        #     _compute_result("assert_synchronous_100_perc_T0_update", global_results["max_update_time"], theoretical_values["synchronous"]["100"]["T0"]["max_update_time"])
        #     _compute_result("assert_synchronous_100_perc_T0_update_sync", global_results_sync["max_update_sync_time"], theoretical_values["synchronous"]["100"]["T0"]["max_update_sync_time"])
        # else:
        #     _compute_result("assert_synchronous_100_perc_T1_deploy", global_results["max_deploy_time"], theoretical_values["synchronous"]["100"]["T1"]["max_deploy_time"])
        #     _compute_result("assert_synchronous_100_perc_T1_deploy_sync", global_results_sync["max_deploy_sync_time"], theoretical_values["synchronous"]["100"]["T1"]["max_deploy_sync_time"])
        #     _compute_result("assert_synchronous_100_perc_T1_update", global_results["max_update_time"], theoretical_values["synchronous"]["100"]["T1"]["max_update_time"])
        #     _compute_result("assert_synchronous_100_perc_T1_update_sync", global_results_sync["max_update_sync_time"], theoretical_values["synchronous"]["100"]["T1"]["max_update_sync_time"])

        print()


# print_duration_delta([
#     "results_synchronous_T0_perc-1-1_waiting_rate-1-2022-12-14_17-52-39.yaml",
# ])
