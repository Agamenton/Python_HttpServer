class WebsiteConfig:
    def __init__(self, name, port, path, run_command, is_static=True, max_users=10):
        self.name = name
        self.port = port
        self.path = path
        self.run_command = run_command
        self.is_static = is_static
        self.max_users = max_users
