import os
from datetime import timezone
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from app.database.db import SessionLocal
from app.database.models import (
    Bill,
    BillItem,
    Product,
    Customer
)


# ============================================================
# CONFIGURATION
# ============================================================

STORE_NAME = "NEBULA SUPERMARKET"

STORE_TIMEZONE = ZoneInfo("Asia/Kolkata")

GENERATED_DIR = "generated"


# ============================================================
# MONEY FORMATTER
# ============================================================

def format_money(amount):
    """
    Format a numeric value as Indian Rupee currency.
    """

    if amount is None:
        amount = 0.0

    return f"₹{float(amount):,.2f}"


# ============================================================
# DATE FORMATTER
# ============================================================

def format_invoice_date(created_at):
    """
    Convert stored UTC datetime into Indian local time.
    """

    if not created_at:
        return "N/A"

    try:

        # Existing database stores naive UTC datetime
        created_at_utc = created_at.replace(
            tzinfo=timezone.utc
        )

        local_time = created_at_utc.astimezone(
            STORE_TIMEZONE
        )

        return local_time.strftime(
            "%d-%m-%Y %I:%M %p"
        )

    except Exception:
        return str(created_at)


# ============================================================
# GENERATE INVOICE
# ============================================================

def generate_invoice(bill_id):
    """
    Generate a PDF invoice for a bill.

    Only finalized bills can generate invoices.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # FIND BILL
        # ====================================================

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill with ID {bill_id} not found."
                )
            }

        # ====================================================
        # ONLY FINALIZED BILLS
        # ====================================================

        if bill.status != "finalized":

            return {
                "success": False,
                "message": (
                    "Invoice can only be generated "
                    "for a finalized bill."
                )
            }

        # ====================================================
        # GET BILL ITEMS
        # ====================================================

        items = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id
            )
            .all()
        )

        if not items:

            return {
                "success": False,
                "message": (
                    "Cannot generate invoice for "
                    "an empty bill."
                )
            }

        # ====================================================
        # CREATE GENERATED DIRECTORY
        # ====================================================

        os.makedirs(
            GENERATED_DIR,
            exist_ok=True
        )

        # ====================================================
        # PDF FILE PATH
        # ====================================================

        filename = (
            f"invoice_{bill.id}.pdf"
        )

        filepath = os.path.join(
            GENERATED_DIR,
            filename
        )

        # ====================================================
        # GET CUSTOMER
        # ====================================================

        customer = None

        if bill.customer_id is not None:

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id == bill.customer_id
                )
                .first()
            )

        # ====================================================
        # PDF DOCUMENT
        # ====================================================

        document = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        # ====================================================
        # STYLES
        # ====================================================

        styles = getSampleStyleSheet()

        store_style = ParagraphStyle(
            "StoreName",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=5
        )

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            "NormalInvoice",
            parent=styles["Normal"],
            fontSize=9,
            leading=12
        )

        right_style = ParagraphStyle(
            "RightInvoice",
            parent=normal_style,
            alignment=TA_RIGHT
        )

        # ====================================================
        # STORY
        # ====================================================

        story = []

        # Store name
        story.append(
            Paragraph(
                STORE_NAME,
                store_style
            )
        )

        story.append(
            Paragraph(
                "TAX INVOICE",
                title_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

        # ====================================================
        # BILL INFORMATION
        # ====================================================

        customer_name = (
            customer.name
            if customer
            else "Walk-in Customer"
        )

        customer_phone = (
            customer.phone
            if customer and customer.phone
            else "-"
        )

        bill_information = [
            [
                Paragraph(
                    f"<b>Bill No:</b> {bill.id}",
                    normal_style
                ),
                Paragraph(
                    f"<b>Date:</b> "
                    f"{format_invoice_date(bill.created_at)}",
                    normal_style
                )
            ],
            [
                Paragraph(
                    f"<b>Customer:</b> "
                    f"{customer_name}",
                    normal_style
                ),
                Paragraph(
                    f"<b>Phone:</b> "
                    f"{customer_phone}",
                    normal_style
                )
            ],
            [
                Paragraph(
                    f"<b>Payment Mode:</b> "
                    f"{bill.payment_mode.upper()}",
                    normal_style
                ),
                Paragraph(
                    f"<b>Status:</b> "
                    f"{bill.status.upper()}",
                    normal_style
                )
            ]
        ]

        information_table = Table(
            bill_information,
            colWidths=[
                85 * mm,
                85 * mm
            ]
        )

        information_table.setStyle(
            TableStyle([
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            information_table
        )

        story.append(
            Spacer(1, 10)
        )

        # ====================================================
        # PRODUCT TABLE
        # ====================================================

        table_data = [
            [
                Paragraph(
                    "<b>Product</b>",
                    normal_style
                ),
                Paragraph(
                    "<b>SKU</b>",
                    normal_style
                ),
                Paragraph(
                    "<b>Qty</b>",
                    right_style
                ),
                Paragraph(
                    "<b>Price</b>",
                    right_style
                ),
                Paragraph(
                    "<b>GST %</b>",
                    right_style
                ),
                Paragraph(
                    "<b>Total</b>",
                    right_style
                )
            ]
        ]

        for item in items:

            product = (
                db.query(Product)
                .filter(
                    Product.id == item.product_id
                )
                .first()
            )

            if not product:

                return {
                    "success": False,
                    "message": (
                        f"Product for bill item "
                        f"{item.id} was not found."
                    )
                }

            table_data.append(
                [
                    Paragraph(
                        product.name,
                        normal_style
                    ),
                    Paragraph(
                        product.sku,
                        normal_style
                    ),
                    Paragraph(
                        str(item.quantity),
                        right_style
                    ),
                    Paragraph(
                        format_money(
                            item.unit_price
                        ),
                        right_style
                    ),
                    Paragraph(
                        f"{item.gst_rate:.2f}%",
                        right_style
                    ),
                    Paragraph(
                        format_money(
                            item.total_amount
                        ),
                        right_style
                    )
                ]
            )

        product_table = Table(
            table_data,
            colWidths=[
                47 * mm,
                24 * mm,
                17 * mm,
                25 * mm,
                20 * mm,
                30 * mm
            ],
            repeatRows=1
        )

        product_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        story.append(
            product_table
        )

        story.append(
            Spacer(1, 15)
        )

        # ====================================================
        # TOTALS
        # ====================================================

        totals_data = [
            [
                Paragraph(
                    "<b>Subtotal</b>",
                    normal_style
                ),
                Paragraph(
                    format_money(
                        bill.subtotal
                    ),
                    right_style
                )
            ],
            [
                Paragraph(
                    "<b>GST</b>",
                    normal_style
                ),
                Paragraph(
                    format_money(
                        bill.gst_amount
                    ),
                    right_style
                )
            ],
            [
                Paragraph(
                    "<b>Grand Total</b>",
                    normal_style
                ),
                Paragraph(
                    f"<b>{format_money(bill.total_amount)}</b>",
                    right_style
                )
            ]
        ]

        totals_table = Table(
            totals_data,
            colWidths=[
                130 * mm,
                33 * mm
            ]
        )

        totals_table.setStyle(
            TableStyle([
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.black
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                )
            ])
        )

        story.append(
            totals_table
        )

        # ====================================================
        # CREDIT INFORMATION
        # ====================================================

        if bill.payment_mode == "credit" and customer:

            story.append(
                Spacer(1, 10)
            )

            story.append(
                Paragraph(
                    (
                        "<b>Khata / Credit Sale:</b> "
                        "This amount has been added to "
                        "the customer's outstanding credit balance."
                    ),
                    normal_style
                )
            )

        # ====================================================
        # FOOTER
        # ====================================================

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                "Thank you for shopping with us!",
                ParagraphStyle(
                    "Footer",
                    parent=normal_style,
                    alignment=TA_CENTER,
                    fontSize=10
                )
            )
        )

        # ====================================================
        # BUILD PDF
        # ====================================================

        document.build(story)

        # ====================================================
        # VERIFY FILE
        # ====================================================

        if not os.path.exists(filepath):

            return {
                "success": False,
                "message": (
                    "Invoice generation completed but "
                    "PDF file was not found."
                )
            }

        file_size = os.path.getsize(
            filepath
        )

        if file_size == 0:

            return {
                "success": False,
                "message": (
                    "Generated PDF file is empty."
                )
            }

        # ====================================================
        # SUCCESS
        # ====================================================

        return {
            "success": True,
            "message": (
                "PDF invoice generated successfully."
            ),
            "bill_id": bill.id,
            "filename": filename,
            "filepath": filepath,
            "file_size": file_size,
            "total_amount": round(
                float(bill.total_amount),
                2
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating invoice: {str(e)}"
            )
        }

    finally:

        db.close()