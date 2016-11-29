$(document).ready(function() {
    if (window.location.hash) {
        var ele = $("a[href='" + window.location.hash + "']");
        if (ele.length && ele.hasClass("nav-link")) {
            ele.click();
        }
    }
    $("#git-pull").click(function() {
        $(this).html("<i class='fa fa-cog fa-spin'></i> Pulling...").prop("disabled", true);
        $.get(git_pull_endpoint, function(data) {
            $("#git-output").text("Process exited with return code " + data.ret + (data.out ? "\n\n" + data.out : "") + (data.err ? "\n\n" + data.err : "")).slideDown("fast");
        }).fail(function(xhr, textStatus, err) {
            $("#git-output").text("Failed to contact server!\n\n" + xhr + "\n" + textStatus + "\n" + err).slideDown("fast");
        }).always(function() {
            $("#git-pull").html("<i class='fa fa-github'></i> Git Pull").prop("disabled", false);
        });
    });
    $("#generate-database-password").click(function(e) {
        if (!confirm("Are you sure you want to regenerate passwords for this database?")) {
            e.preventDefault();
        }
    });
    $("#generate-key").click(function(e) {
        if ($(this).text().indexOf("Regenerate") > -1) {
            if (!confirm("Are you sure you want to regenerate keys for this site?")) {
                e.preventDefault();
            }
        }
    });
});
var select = function(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}
