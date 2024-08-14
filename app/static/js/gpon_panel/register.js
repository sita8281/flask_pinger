function autofindGpon(gpon_name) {
    $.ajax({
        type: "post",
        url: "/gpon_panel/autofind/" + gpon_name,
        timeout: 60000,
        dataType: "json",
        success: function (response) {
            
        },
        error: function (err) {
            
        }
    });
}