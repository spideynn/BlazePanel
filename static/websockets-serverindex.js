function update_values() {
    $.getJSON($SCRIPT_ROOT+"/_stuff",
        function(data) {
            $("#cpuload").text(data.cpu+" %")
            $("#ram").text(data.ram.percentage + " %")
            $("#pid").text("PID: " + data.pid)
            $('.progress-bar').css('width', valeur+'%').attr('aria-valuenow', data.ram.percentage);
    });
}