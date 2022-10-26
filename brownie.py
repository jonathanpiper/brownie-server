import myriad_class
import asyncio
import websockets
import json
import signal
import sys


def sigint_handler(signal, frame):
    print("Exiting.")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

# “cmd –0\r” Get Current Status Information
# “cmd –1\r” Get Current Status Information
# V001 XXXX Mute_Status(0, 1) Smart_Volume(0,1) Volume_Pot(0,1) Smart_Volume_Register Direct_Volume_Register Current_Pot_Reading Level_Min Level_Max Response_Timer Level_Max Response_Time
# V001 0D63 1 1 0 148 0 2484 109 168 49 3 512
# “cmd –t\r” Get Current Status Information

commands = {
    "status": "0",
    "settings": "1",
    "mute_off": "m",
    "mute_on": "M",
    "smvol_off": "v",
    "smvol_on": "V",
    "volpot_on": "r",
    "volpot_off": "R",
}
registers = {"smvol": "03", "levelmax": "04", "levelmin": "05", "responsetime": "07"}
ret_values = {
    "0": [
        "cur_mic",
        "cur_amb",
        "cur_input",
        "cur_output",
        "a",
        "volpot_register",
        "b",
        "c",
        "d",
    ],
    "1": [
        "mute_switch",
        "smvol_switch",
        "volpot_switch",
        "smvol_register",
        "dirvol_register",
        "volpot_register",
        "level_min",
        "level_max",
        "response_time",
        "a",
        "b",
    ],
}

myriadAmp = myriad_class.MyriadAmpConnection()


def get_myriad_values(command):
    ro = {}
    res = myriadAmp.send_command(commands[command])
    res_arr = []
    if len(res) > 0:
        if res[0] == "V":
            res_arr = res.split(" ")[1:]
            res_arr[:] = [x for x in res_arr if "\r" not in x]
            if len(res_arr) - 1 == len(ret_values[commands[command]]):
                try:
                    if len(res_arr[0]) == 4:
                        ro["seq_no"] = res_arr.pop(0)
                except:
                    exit
                for ret_val in ret_values[commands[command]]:
                    try:
                        if len(res_arr[0]) > 0:
                            ro[ret_val] = res_arr.pop(0)
                    except:
                        ro[ret_val] = "err"
                        exit
    if ro != {}:
        return ro
    else:
        return "Unable to parse output."


async def handler(websocket):
    while True:
        try:
            m = await websocket.recv()
            message = json.loads(m)
            for k, v in message.items():
                if k == "request":
                    if v == "settings":
                        await websocket.send(json.dumps(get_myriad_values("settings")))
                    if v == "status":
                        await websocket.send(json.dumps(get_myriad_values("status")))
                if k == "set":
                    if v in commands:
                        print("Setting flag " + commands[v])
                        myriadAmp.send_command(commands[v])
                    else:
                        [c, p] = v.split("_")
                        print("Setting " + c + " to " + p)
                        cmd = (
                            "L"
                            + registers[c]
                            + "00"
                            + str(hex(int(p)).split("x")[-1]).upper().rjust(2, "0")
                        )
                        myriadAmp.send_command(cmd)
                    await websocket.send(json.dumps(get_myriad_values("settings")))
        except websockets.exceptions.ConnectionClosedOK as e:
            await asyncio.sleep(0.01)


async def main():
    async with websockets.serve(handler, "", 8080):
        await asyncio.Future()


if __name__ == "__main__":
    print("Lauching Brownie.")
    asyncio.run(main())
