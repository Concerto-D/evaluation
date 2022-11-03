for i in {1..51}; do
    ssh nancy.grid5000.fr "ssh-keyscan -t rsa grisou-$i" >> ~/.ssh/known_hosts
done

