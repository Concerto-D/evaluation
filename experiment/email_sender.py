# Import smtplib for the actual sending function
import smtplib
import ssl
from email.mime.text import MIMEText

# Import the email modules we'll need
from email.message import EmailMessage


def send_email_expe_finished(expe_name, sweeper_state_str, sweeper_params, local_expe_res_dir, email_parameters):
    smtp_server, smtp_port, username, password = email_parameters.values()

    msg = EmailMessage()
    msg_content = f"Experiment {expe_name} finished:\n"
    msg_content += sweeper_state_str + "\n"
    msg_content += str(sweeper_params) + "\n"
    msg_content += f"Results saved directory: /home/aomond/experiments_results/{local_expe_res_dir}"
    msg.set_content(MIMEText(msg_content))

    msg['Subject'] = f"Experiment {expe_name} finished"
    msg['From'] = "antoine.omond@imt-atlantique.fr"
    msg['To'] = "antoine.omond@imt-atlantique.fr"

    # Send the message via our own SMTP server.
    context = ssl.create_default_context()
    s = smtplib.SMTP(
        host=smtp_server,
        port=smtp_port
    )
    s.starttls(context=context)
    s.login(username, password)
    s.send_message(msg)
    s.quit()
