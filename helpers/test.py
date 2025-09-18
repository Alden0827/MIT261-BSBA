def go():


	print(go.__name__)

go()

I WANT YOU TO CREATE A PYTHON SCRIPT THAT WILL DO THE FOLLOWING
1. get the list of teachers (unique) from subjects.Teacher
2. create a username from the teacher name like "Prof. Tony Lim" to "prof_tlim" and password = 'password' default
3. for password use      def generate_password_hash(self,password: str) -> bytes:
        """
        Generates a bcrypt hash for a given plain-text password.

        Args:
            password (str): The plain-text password to hash.

        Returns:
            bytes: The hashed password as bytes (compatible with verify_password).
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed
4. insert the username and password to userAccounts collection


userAccounts sample data
{
  "username": "prof_tlim",
  "role": "teacher",
  "linkedId": 1,
  "passwordHash": {
    "$binary": {
      "base64": "JDJiJDEyJFFSTGVveC5UYVdmRlRjUzdpa0c1Z09sVGhWeEkxcWpGQWs1V1oveGlQNDl3RmFDelgybnBt",
      "subType": "00"
    }
  },
  "fullName": "", # teacher fullname
  "UID": Null
}