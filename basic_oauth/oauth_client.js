;(function(window) {

    if (window.jQuery === undefined) {
        console.log('Cannot load the form: jQuery is not found');
        return;
    }

    $(window.document).ready(function () {
        loadForms();
    });

    var loadForms = function () {
        var target = $('form.oauth');
        // Override the form submit with the oauth authentication
        target.submit(function () {
            var username = target.find('input[name=username]').val(),
                password = target.find('input[name=password]').val();
            $.ajax({
                url: target.attr('action'),
                type: 'POST',
                data: {
                    'grant_type': 'password',
                    'username': username,
                    'password': password
                },
                complete: function (jqXHR, textStatus) {
                    if (window.oauthResponseHandler === undefined) {
                        return
                    }
                    response = JSON.parse(jqXHR.responseText);
                    window.oauthResponseHandler(response);
                }
            });
            return false;
        });
    };

})(window);
