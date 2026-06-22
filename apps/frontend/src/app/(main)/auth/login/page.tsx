import Image from "next/image";

import { LoginForm } from "../_components/login-form";

export default function LoginPage() {
  return (
    <div className="flex h-dvh">
      <div className="hidden bg-primary lg:block lg:w-1/3">
        <div className="flex h-full flex-col items-center justify-center p-12 text-center">
          <div className="space-y-2">
            <h1 className="font-light text-5xl text-primary-foreground">Content de te revoir</h1>
            <p className="text-primary-foreground/80 text-xl">Connecte-toi pour continuer</p>
          </div>
        </div>
      </div>

      <div className="flex w-full items-center justify-center bg-background p-8 lg:w-2/3">
        <div className="w-full max-w-md space-y-10 py-24 lg:py-32">
          <div className="space-y-4 text-center">
            <Image src="/logo.png" alt="Externam Studio Hub" width={80} height={80} priority className="mx-auto h-20 w-20" />
            <div className="font-medium text-lg tracking-tight">Connexion à Externam Studio Hub</div>
          </div>
          <div className="space-y-4">
            <LoginForm />
          </div>
        </div>
      </div>
    </div>
  );
}
