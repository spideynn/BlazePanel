$(document).ready(function () {
    function update_values() {
        $.getJSON("_api", function (data) {
            $("#cpu-progress").css("width", data.cpu + "%").attr("aria-valuenow", data.cpu).text(data.cpu + "%");
            $("#memory-progress").css("width", data.ram[2] + "%").attr("aria-valuenow", data.ram[2]).text(data.ram[2] + "%");
            $("#server-pid").text("PID: " + data.pid)
        });
    }

    setInterval(function () {
        update_values();
    }, 2000);
});


function startServer() {
    //$.post("_start")
}

function stopServer() {
    //$.post("_stop")
}

function restartServer() {
    //$.post("_restart")
}