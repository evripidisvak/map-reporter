$(document).ready(function () {
    // Setup - add a text input to each footer cell
    $('#all-products-table thead tr:eq(1) th').each(function () {
        var title = $(this).text();
        if (! $(this).hasClass('no_filter')) {
            $(this).html('<input type="text" placeholder="Search ' + title + '" class="column_search_all-products-table table-filter-input" />');
        }
    });

    // DataTable
    var all_products_table = $('#all-products-table').DataTable({
        orderCellsTop: true,
        scrollX: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print'
        ],
        initComplete: function () {
            this.api().columns('.add_select').every(function () {
                var column = this;
                var select = $('<select><option value=""></option></select>')
                    .appendTo($("#all-products-table thead tr:eq(1) th").eq(column.index()).empty())
                    .on('change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );
                        column
                            .search(val ? '^' + val + '$' : '', true, false)
                            .draw();
                    });

                column.data().unique().sort().each(function (d, j) {
                    const regex = /(<([^>]+)>)/ig;
                    d = d.replace(regex, "");
                    select.append('<option value="' + d + '">' + d + '</option>');
                });
            });
        }
    });

    // Apply the search
    $('#all-products-table thead').on('keyup', ".column_search_all-products-table", function () {
        all_products_table
            .column($(this).parent().index())
            .search(this.value)
            .draw();
    });

    // Setup - add a text input to each footer cell
    $('#all-products-prices-table thead tr:eq(1) th').each(function () {
        var title = $(this).text();
        if (! $(this).hasClass('no_filter')) {
            $(this).html('<input type="text" placeholder="Search ' + title + '" class="column_search_all-products-prices-table table-filter-input" />');
        }
    });

    // DataTable
    var active_products_table = $('#all-products-prices-table').DataTable({
        orderCellsTop: true,
        scrollX: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print'
        ],
        initComplete: function () {
            this.api().columns('.add_select').every(function () {
                var column = this;
                var select = $('<select><option value=""></option></select>')
                    .appendTo($("#all-products-prices-table thead tr:eq(1) th").eq(column.index()).empty())
                    .on('change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        column
                            .search(val ? '^' + val + '$' : '', true, false)
                            .draw();
                    });

                column.data().unique().sort().each(function (d, j) {
                    const regex = /(<([^>]+)>)/ig;
                    d = d.replace(regex, "");
                    select.append('<option value="' + d + '">' + d + '</option>');
                });
            });
        }
    });

    // Apply the search
    $('#all-products-prices-table thead').on('keyup', ".column_search_all-products-prices-table", function () {
        active_products_table
            .column($(this).parent().index())
            .search(this.value)
            .draw();
    });

});


