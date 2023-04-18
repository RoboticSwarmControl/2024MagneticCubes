import slurminade

slurminade.update_default_configuration(
    partition="alg",
    constraint="alggen03",
    mail_user="k.keune@tu-braunschweig.de",
    mail_type="ALL",
)

@slurminade.slurmify()
def hardWork(n, text):
    with open("../results/slurm_test.txt", "w") as file:
        for i in range(n):
            file.write(f"{i} time writing '{text}'")
    print("Done!")

if __name__ == "__main__":
    hardWork.distribute(100, "This text is a text that was written for testing to write a text.")