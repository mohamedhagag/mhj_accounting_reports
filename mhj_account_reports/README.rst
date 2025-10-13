====================================
Hajjaj.Pro AccountingFinancial Reports
====================================

This Module will provide all the financial reports for odoo 
community edition with performance optimizations for handling millions of journal items.

Installation
============

To install this module, you need to:

Download the module and add it to your Odoo addons folder. Afterward, log on to
your Odoo server and go to the Apps menu. Trigger the debug mode and update the
list by clicking on the "Update Apps List" link. Now install the module by
clicking on the install button.

Upgrade
============

To upgrade this module, you need to:

Download the module and add it to your Odoo addons folder. Restart the server
and log on to your Odoo server. Select the Apps menu and upgrade the module by
clicking on the upgrade button.


Configuration
=============

Performance Optimization
------------------------

For databases with millions of journal items, this module includes advanced 
performance optimizations:

* **Memory Management**: Batch processing and pagination to avoid out-of-memory issues
* **Database Optimization**: Automatic index creation and query optimization
* **Configurable Limits**: Control batch sizes and record limits per report
* **Memory Monitoring**: Built-in tracking of memory usage during report generation

This module Automatically performs the following optimizations:

1. Create performance database indexes
2. Update table statistics  
3. Monitor database health

Performance Settings
-------------------

Each report wizard includes performance options:

* **Enable Pagination**: Process data in batches (recommended for large datasets)
* **Max Records per Account**: Limit journal entries per account (default: 50,000)
* **Batch Size**: Records processed per batch (default: 10,000)

See PERFORMANCE_GUIDE.md for detailed optimization guidelines.


Credits
=======

Contributors
------------

* Hajjaj.Pro <odooapps@hajjaj.pro>


Author & Maintainer
-------------------

This module is maintained by the Hajjaj.Pro