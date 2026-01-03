from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
import ssl


class CustomEmailBackend(SMTPBackend):
    def open(self):
        if self.connection:
            return False

        connection_params = {}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout

        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            if self.use_tls:
                # Use unverified SSL context
                context = ssl._create_unverified_context()
                self.connection.starttls(context=context)

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception:
            if not self.fail_silently:
                raise