from .CodesDashboard import CodesDashboard

def main(server=None, **kwargs):
    app = CodesDashboard(server)
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()