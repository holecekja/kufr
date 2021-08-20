"use strict";

const kufr = {}

kufr.url = function() {
    return window.location.href
}

kufr.encode = (string) => {
    return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

kufr.request_custom = async function(method, route, parameters, handler) {
    let requestURL = kufr.url() + route

    if (parameters && Object.keys(parameters).length != 0) {
        requestURL += "?"

        for (const [key, value] of Object.entries(parameters)) {
            requestURL += encodeURIComponent(key) + "=" + encodeURIComponent(value.toString()) + ";"
        }

        requestURL = requestURL.slice(0, -1)
    }
    
    const response = await fetch(requestURL, {
        method: method,
        body: "",
        credentials: "include",
        headers: {
            'Content-Type': 'application/json'
        }
    })
    handler(response)
}

kufr.request_json = function(route, parameters=null, handler=null) {
    kufr.request_custom("POST", route, parameters, async function(response){
        if (handler)
            handler(await response.json())
    })
}

kufr.request_text = function(route, parameters=null, handler=null) {
    kufr.request_custom("POST", route, parameters, async function(response){
        if (handler)
            handler(await response.text())
    })
}

kufr.update_state = (state) => {
    kufr.state = state
}

kufr.request_state = () => {
    kufr.request_json("getState", null, kufr.update_state)
}

kufr.update_element = (element, text) => {
    const elem = document.getElementById(element)
    if (elem && elem.innerHTML != text)
        elem.innerHTML = kufr.encode(text)
}

kufr.update_content = () => {
    if (!kufr.state)
        return;

    kufr.update_element("word", kufr.state.word)
    kufr.update_element("points", kufr.state.points.toString())

    if (kufr.state.started) {
        const now = kufr.state.paused ? kufr.state.pausedAt * 1000.0 : Date.now()
        const started = kufr.state.startTime * 1000.0 // sent time is in fractional seconds
        const elapsed = now - started
        const roundDuration = kufr.state.roundDuration * 1000.0
        const remaining = roundDuration - elapsed

        if (remaining < 0)
            kufr.update_element("timer", "0")
        else
            kufr.update_element("timer", Math.floor(remaining / 1000).toString())
    }
    else {
        kufr.update_element("timer", "")
    }

    kufr.update_element("status", kufr.state.status)
}

kufr.create_refresh_timers = () => {
    setInterval(kufr.request_state, 300)
    setInterval(kufr.update_content, 100)
}

kufr.isAuthorized = (onComplete) => {
    kufr.request_json("isAuthorized", null, (response)=>{
        if (onComplete)
            onComplete(response.authorized)
    })
}

kufr.tryAuthorize = () => {
    const password = prompt("Please enter the password")
    kufr.request_json("authorize", {"password": password}, (response)=>{
        if (!response.success)
            alert("Incorrect password")
    })
}

kufr.on_load = function() {
    kufr.create_refresh_timers()

    kufr.isAuthorized((authorized) => {
        if (!authorized) {
            kufr.tryAuthorize()
        }
    })
}