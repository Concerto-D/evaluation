import time

from execo_engine import sweep, ParamSweeper

sweeps = sweep({
    "list1": ["un", "deux"],
    "list2": [1, 2]
})

sweeper = ParamSweeper(
    persistence_dir="sweeper_test", sweeps=sweeps,
    save_sweeps=True
)

parameter = sweeper.get_next()
while parameter:
    try:
        print(f"doing param {parameter}")
        time.sleep(1)
        for i in range(10000000000):
            l = [1,2,3]
        raise Exception
        sweeper.done(parameter)
    except Exception as e:
        print(f"expection while doing param {parameter}")
        sweeper.skip(parameter)
    finally:
        print("getting next param")
        parameter = sweeper.get_next()
