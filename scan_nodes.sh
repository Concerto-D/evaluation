for i in {1..51}; do
    ssh nancy.grid5000.fr "ssh-keyscan grisou-$i.nancy.grid5000.fr" >> ~/.ssh/known_hosts
done

