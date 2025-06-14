import base64
from typing import Union

class SimpleEncryption:
    """Simple encryption implementation for applicant data (Bonus Feature)"""
    
    def __init__(self, key: str = "StimaSukses2024"):
        self.key = key.encode('utf-8')
        self.key_length = len(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data using simple XOR cipher with base64 encoding"""
        if not data:
            return ""
        
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()
        
        for i, byte in enumerate(data_bytes):
            key_byte = self.key[i % self.key_length]
            encrypted.append(byte ^ key_byte)
        
        # Add simple obfuscation
        obfuscated = self._obfuscate(encrypted)
        
        # Base64 encode for safe storage
        return base64.b64encode(obfuscated).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""
        
        try:
            # Base64 decode
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Remove obfuscation
            deobfuscated = self._deobfuscate(decoded)
            
            # XOR decrypt
            decrypted = bytearray()
            for i, byte in enumerate(deobfuscated):
                key_byte = self.key[i % self.key_length]
                decrypted.append(byte ^ key_byte)
            
            return decrypted.decode('utf-8')
        except Exception:
            return ""
    
    def _obfuscate(self, data: bytearray) -> bytearray:
        """Simple obfuscation by byte rotation"""
        obfuscated = bytearray()
        for i, byte in enumerate(data):
            # Rotate bits based on position
            rotation = (i % 8)
            rotated = ((byte << rotation) | (byte >> (8 - rotation))) & 0xFF
            obfuscated.append(rotated)
        return obfuscated
    
    def _deobfuscate(self, data: bytes) -> bytearray:
        """Reverse obfuscation"""
        deobfuscated = bytearray()
        for i, byte in enumerate(data):
            # Reverse rotation
            rotation = (i % 8)
            unrotated = ((byte >> rotation) | (byte << (8 - rotation))) & 0xFF
            deobfuscated.append(unrotated)
        return deobfuscated
    
    def encrypt_profile_data(self, profile_data: dict) -> dict:
        """Encrypt sensitive profile data"""
        encrypted_data = {}
        sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        
        for key, value in profile_data.items():
            if key in sensitive_fields and value:
                encrypted_data[key] = self.encrypt(str(value))
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def decrypt_profile_data(self, encrypted_data: dict) -> dict:
        """Decrypt sensitive profile data"""
        decrypted_data = {}
        sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        
        for key, value in encrypted_data.items():
            if key in sensitive_fields and value:
                decrypted_data[key] = self.decrypt(str(value))
            else:
                decrypted_data[key] = value
        
        return decrypted_data

# Test function
def test_encryption():
    """Test encryption functionality"""
    encryptor = SimpleEncryption()
    
    test_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@email.com',
        'phone_number': '+1234567890',
        'address': '123 Main Street',
        'applicant_id': 1  # This won't be encrypted
    }
    
    print("Original data:", test_data)
    
    # Encrypt
    encrypted = encryptor.encrypt_profile_data(test_data)
    print("Encrypted data:", encrypted)
    
    # Decrypt
    decrypted = encryptor.decrypt_profile_data(encrypted)
    print("Decrypted data:", decrypted)
    
    # Verify
    print("Encryption/Decryption successful:", decrypted == test_data)

if __name__ == "__main__":
    test_encryption()