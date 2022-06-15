
$(document).ready(function () {
    // Setup - add a text input to each footer cell
    $('#shops-table thead tr:eq(1) th').each(function () {
        var title = $(this).text();
        $(this).html('<input type="text" placeholder="Search ' + title + '" class="column_search" />');
    });

    // DataTable
    var table = $('#shops-table').DataTable({
        orderCellsTop: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print'
        ],
        initComplete: function () {
            this.api().columns('.add_select').every(function () {
                var column = this;
                var select = $('<select><option value=""></option></select>')
                    .appendTo($("#shops-table thead tr:eq(1) th").eq(column.index()).empty())
                    .on('change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );
                        column
                            .search(val ? '^' + val + '$' : '', true, false)
                            .draw();
                    });

                column.data().unique().sort().each(function (d, j) {
                    select.append('<option value="' + d + '">' + d + '</option>');
                });
            });
        }
    });

    // Apply the search
    $('#shops-table thead').on('keyup', ".column_search", function () {
        table
            .column($(this).parent().index())
            .search(this.value)
            .draw();
    });

});
