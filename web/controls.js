"use strict";

kufr.next = () => {
    kufr.request_json("nextWord")
}

kufr.skip = () => {
    kufr.request_json("skipWord")
}

kufr.nuke = () => {
    if (confirm("Are you sure? This will make all the configured words available again!"))
        kufr.request_json("nukeUsedWords")
}

kufr.reset = () => {
    if (confirm("Are you sure? This will reset the game state!"))
        kufr.request_json("reset")
}

kufr.start = () => {
    kufr.request_json("start")
}

kufr.pause = () => {
    kufr.request_json("pause")
}

kufr.resume = () => {
    kufr.request_json("resume")
}

kufr.modifyPoints = (points) => {
    kufr.request_json("modifyPoints", {"points":points})
}

kufr.modifyTimer = (seconds) => {
    kufr.request_json("modifyTimer", {"seconds":seconds})
}