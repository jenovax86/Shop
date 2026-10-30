from sessions.models import Session


def create_session(user, user_agent, expires_at):
    return Session.objects.create(user=user, user_agent=user_agent, expires_at=expires_at)
