import '../style/service_form.less'

$(document).ready(function () {
    $(".field.service-urls").each(function () {
        var previous = null;
        var previousEmpty = false;
        $(this).find("input").each(function () {
            if (previous !== null) {
                $(previous).keyup((function (next, current) {
                    return function () {
                        if ($(current).val()) {
                            $(next).show();
                        } else {
                            $(next).hide();
                        }
                    }
                })(this, previous));
            }
            var isEmpty = $(this).val() == "";
            if (isEmpty && previousEmpty) {
                $(this).hide();
            }
            previous = this;
            previousEmpty = isEmpty;
        });
    });

    $(".field.name input:visible").prop("required", true);
});

$("button.remove-environment").click(function () {
    var checkbox = $("#" + $(this).data("checkbox"));
    checkbox.val(true);

    var uiSegment = checkbox.closest(".ui.segment");
    uiSegment.hide();
    uiSegment.find(".field.name input").prop("required", false);

    var hidden = $(".ui.segment.environment:hidden");
    if (hidden.length > 0) {
        $("button.add-environment").prop("disabled", false);
    }
});

$("button.remove-link").click(function () {
    var checkbox = $("#" + $(this).data("checkbox"));
    checkbox.val(true);

    var uiSegment = checkbox.closest(".ui.segment");
    uiSegment.hide();
    uiSegment.find(".field.name input").prop("required", false);

    var hidden = $(".ui.segment.link:hidden");
    if (hidden.length > 0) {
        $("button.add-link").prop("disabled", false);
    }
});

$("button.add-environment").click(function () {
    $(this).blur();
    var hidden = $(".ui.segment.environment:hidden");
    if (hidden.length > 0) {
        if (hidden.length == 1) {
            $(this).prop("disabled", true);
        }

        var firstSegment = hidden.eq(0);
        firstSegment.find(":not(.no-reset) input").val("");
        firstSegment.find(".field.name input").prop("required", true);
        firstSegment.show();
    }
});
$("button.add-link").click(function () {
    $(this).blur();
    var hidden = $(".ui.segment.link:hidden");
    if (hidden.length > 0) {
        if (hidden.length == 1) {
            $(this).prop("disabled", true);
        }

        var firstSegment = hidden.eq(0);
        firstSegment.find(":not(.no-reset) input").val("");
        firstSegment.find(".field.name input").prop("required", true);
        firstSegment.show();
    }
});

$('.icon-hint .label').popup({
    transition: 'fade down',
    exclusive: true,
    hoverable: true,
    variation: 'inverted',
    position: 'left center'
});
