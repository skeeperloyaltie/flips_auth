import os
import subprocess
import tempfile
import logging
import shutil
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_invoice_pdf(payment):
    # LaTeX template for the invoice
    latex_template = r"""
    \documentclass[a4paper,12pt]{article}
    \usepackage[utf8]{inputenc}
    \usepackage{geometry}
    \usepackage{booktabs}
    \usepackage{fancyhdr}
    \usepackage{lastpage}
    \usepackage{graphicx}
    \geometry{margin=1in}
    \pagestyle{fancy}
    \fancyhf{}
    \lhead{\textbf{FLIPS Invoice}}
    \rhead{Page \thepage\ of \pageref{LastPage}}
    \cfoot{\small FLIPS Intelligence, Nairobi, Kenya}
    \begin{document}
    \begin{center}
        \Huge \textbf{Payment Invoice} \\
        \vspace{0.5cm}
        \large Issued on: \today \\
        \vspace{0.3cm}
        % \includegraphics[width=0.3\textwidth]{logo.png} % Uncomment if logo is used
    \end{center}
    \vspace{0.5cm}
    \noindent
    \textbf{To:} \\
    {user_full_name} \\
    {user_email} \\
    \vspace{0.3cm}
    \textbf{From:} \\
    FLIPS Intelligence \\
    Nairobi, Kenya \\
    Email: flipsintelligence@gmail.com \\
    Phone: +254 700 168 812 \\
    \vspace{0.5cm}
    \begin{tabular}{ll}
        \toprule
        \textbf{Field} & \textbf{Details} \\
        \midrule
        Invoice ID & {unique_reference} \\
        Plan & {plan_name} \\
        Amount & KES {amount} \\
        Payment Type & {payment_type} \\
        {extra_fields}
        \bottomrule
    \end{tabular}
    \vspace{0.5cm}
    \noindent
    Thank you for your subscription. For any inquiries, contact us at flipsintelligence@gmail.com.
    \end{document}
    """

    # Escape special LaTeX characters
    def escape_latex(text):
        if not text:
            return text
        chars = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
            '{': r'\{', '}': r'\}', '~': r'\textasciitilde', '^': r'\textasciicircum',
            '\\': r'\textbackslash'
        }
        for k, v in chars.items():
            text = text.replace(k, v)
        return text

    # Prepare dynamic data
    user_full_name = escape_latex(payment.user.get_full_name() or payment.user.username)
    user_email = escape_latex(payment.user.email)
    plan_name = escape_latex(payment.plan.name)
    amount = f"{payment.amount:.2f}"
    payment_type = escape_latex(payment.get_payment_type_display())
    unique_reference = escape_latex(payment.unique_reference)

    # Extra fields based on payment type
    extra_fields = ""
    if payment.payment_type in ['paybill', 'stk_push']:
        extra_fields += f"Paybill Number & {escape_latex(payment.paybill_number) or 'N/A'} \\\\ \n"
        extra_fields += f"Account Number & {escape_latex(payment.account_number) or 'N/A'} \\\\ \n"
        extra_fields += f"{'Transaction ID' if payment.payment_type == 'paybill' else 'Checkout Request ID'} & {escape_latex(payment.transaction_id) or 'N/A'} \\\\ \n"
    elif payment.payment_type == 'free':
        extra_fields += f"Transaction ID & {escape_latex(payment.transaction_id) or 'N/A'} \\\\ \n"

    # Format the LaTeX template
    latex_content = latex_template.format(
        user_full_name=user_full_name,
        user_email=user_email,
        unique_reference=unique_reference,
        plan_name=plan_name,
        amount=amount,
        payment_type=payment_type,
        extra_fields=extra_fields
    )

    # Create temporary directory for LaTeX compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file_path = os.path.join(temp_dir, "invoice.tex")
        pdf_file_path = os.path.join(temp_dir, "invoice.pdf")

        # Write LaTeX content to file
        with open(tex_file_path, 'w', encoding='utf-8') as tex_file:
            tex_file.write(latex_content)

        # Copy logo to temp directory (if used)
        logo_path = os.path.join(settings.BASE_DIR, 'assets', 'img', 'logo.png')
        if os.path.exists(logo_path):
            shutil.copy(logo_path, os.path.join(temp_dir, 'logo.png'))

        # Compile LaTeX to PDF
        try:
            result = subprocess.run(
                ['pdflatex', '-output-directory', temp_dir, tex_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error(f"LaTeX compilation failed: {result.stderr}")
                raise Exception(f"LaTeX compilation failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("LaTeX compilation timed out")
            raise Exception("LaTeX compilation timed out")
        except FileNotFoundError:
            logger.error("pdflatex not found. Ensure LaTeX is installed.")
            raise Exception("pdflatex not found. Please install a LaTeX distribution.")

        # Check if PDF was generated
        if not os.path.exists(pdf_file_path):
            logger.error("PDF file not generated")
            raise Exception("Failed to generate PDF file")

        # Move PDF to a persistent temporary file
        final_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        shutil.move(pdf_file_path, final_pdf_path)

    return final_pdf_path

def send_invoice_email(payment, pdf_path):
    subject = "FLIPS Payment Invoice"
    message = f"""
        Dear {payment.user.get_full_name() or payment.user.username},

        Thank you for subscribing to the {payment.plan.name} plan. Please find your invoice attached.

        Payment Details:
        - Plan: {payment.plan.name}
        - Amount: KES {payment.amount}
        - Invoice ID: {payment.unique_reference}
        - Payment Type: {payment.get_payment_type_display()}
    """
    if payment.payment_type in ['paybill', 'stk_push']:
        message += f"""
            - Paybill Number: {payment.paybill_number or 'N/A'}
            - Account Number: {payment.account_number or 'N/A'}
        """
        if payment.payment_type == 'paybill':
            message += f"- Transaction ID: {payment.transaction_id}\n"
        else:
            message += f"- Checkout Request ID: {payment.transaction_id}\n"
            message += "Please check your phone to complete the STK Push payment.\n"
            message += "Please verify your payment using the Transaction ID in the verification portal.\n"
    elif payment.payment_type == 'free':
        message += f"- Transaction ID: {payment.transaction_id}\n"
        message += "Your free subscription is active for 14 days.\n"
    message += "\nRegards,\nFLIPS Team"

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email="flipsintelligence@gmail.com",
        to=[payment.user.email],
    )
    email.attach_file(pdf_path)
    try:
        email.send()
        logger.info(f"Invoice email sent to {payment.user.email} for payment {payment.unique_reference}")
    except Exception as e:
        logger.error(f"Failed to send invoice email to {payment.user.email}: {str(e)}")
        raise