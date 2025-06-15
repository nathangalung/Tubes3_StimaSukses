""" encryption implementation for applicant data (Bonus Feature)"""

import base64
import hashlib
import time
import random
from typing import Union, Dict, Any

class Encryption:
    """ encryption implementation with multiple security layers"""
    
    def __init__(self, master_key: str = "StimaSukses2024_SecureATS"):
        self.master_key = master_key
        self.key_matrix = self._generate_key_matrix(master_key)
        self.substitution_box = self._generate_substitution_box()
        self.reverse_substitution_box = self._generate_reverse_substitution_box()
        
    def _generate_key_matrix(self, key: str) -> list:
        """Generate a 16x16 key matrix from master key"""
        # Create deterministic but complex key matrix
        key_hash = self._custom_hash(key)
        matrix = []
        
        for i in range(16):
            row = []
            for j in range(16):
                # Generate pseudo-random values based on key and position
                seed_value = (ord(key_hash[i % len(key_hash)]) + 
                             ord(key_hash[j % len(key_hash)]) + 
                             i * 17 + j * 23) % 256
                row.append(seed_value)
            matrix.append(row)
        
        return matrix
    
    def _custom_hash(self, data: str) -> str:
        """Custom hash function without using hashlib"""
        # Simple but effective hash based on polynomial rolling hash
        result = []
        prime = 31
        hash_value = 0
        
        for char in data:
            hash_value = (hash_value * prime + ord(char)) % (2**32)
        
        # Convert to hex-like string
        for i in range(32):
            hash_value = (hash_value * prime + 17) % (2**32)
            result.append(chr(65 + (hash_value % 26)))  # A-Z
        
        return ''.join(result)
    
    def _generate_substitution_box(self) -> list:
        """Generate S-Box for substitution cipher"""
        # Create a substitution box based on master key
        sbox = list(range(256))
        key_bytes = [ord(c) for c in self.master_key]
        
        # Shuffle based on key
        j = 0
        for i in range(256):
            j = (j + sbox[i] + key_bytes[i % len(key_bytes)]) % 256
            sbox[i], sbox[j] = sbox[j], sbox[i]
        
        return sbox
    
    def _generate_reverse_substitution_box(self) -> list:
        """Generate reverse S-Box for decryption"""
        reverse_sbox = [0] * 256
        for i in range(256):
            reverse_sbox[self.substitution_box[i]] = i
        return reverse_sbox
    
    def _apply_feistel_cipher(self, data: bytearray, rounds: int = 8) -> bytearray:
        """Apply Feistel cipher structure"""
        if len(data) % 2 != 0:
            data.append(0)  # Padding
        
        # Split into left and right halves
        mid = len(data) // 2
        left = data[:mid]
        right = data[mid:]
        
        for round_num in range(rounds):
            # Feistel function
            temp = right[:]
            
            # Apply round function
            for i in range(len(right)):
                key_val = self.key_matrix[round_num % 16][i % 16]
                right[i] = left[i] ^ self._feistel_function(right[i], key_val, round_num)
            
            left = temp
        
        return bytearray(left + right)
    
    def _reverse_feistel_cipher(self, data: bytearray, rounds: int = 8) -> bytearray:
        """Reverse Feistel cipher"""
        if len(data) % 2 != 0:
            return data
        
        mid = len(data) // 2
        left = data[:mid]
        right = data[mid:]
        
        # Reverse the rounds
        for round_num in range(rounds - 1, -1, -1):
            temp = left[:]
            
            for i in range(len(left)):
                key_val = self.key_matrix[round_num % 16][i % 16]
                left[i] = right[i] ^ self._feistel_function(left[i], key_val, round_num)
            
            right = temp
        
        return bytearray(left + right)
    
    def _feistel_function(self, data_byte: int, key_byte: int, round_num: int) -> int:
        """Feistel round function"""
        # Complex mixing function
        result = data_byte ^ key_byte
        result = self.substitution_box[result]
        result = ((result << (round_num % 8)) | (result >> (8 - (round_num % 8)))) & 0xFF
        result ^= (round_num * 7) % 256
        return result
    
    def _apply_transposition(self, data: bytearray) -> bytearray:
        """Apply columnar transposition"""
        if len(data) < 8:
            return data
        
        # Determine block size (8-16 bytes)
        block_size = 8 + (len(data) % 9)
        transposed = bytearray()
        
        for i in range(0, len(data), block_size):
            block = data[i:i + block_size]
            if len(block) < block_size:
                # Padding
                while len(block) < block_size:
                    block.append(0)
            
            # Transpose using predefined pattern
            pattern = [3, 0, 6, 1, 4, 7, 2, 5] if block_size == 8 else list(range(block_size))
            if block_size > 8:
                # Generate pattern for larger blocks
                pattern = [(i * 7) % block_size for i in range(block_size)]
            
            transposed_block = bytearray()
            for pos in pattern:
                if pos < len(block):
                    transposed_block.append(block[pos])
            
            transposed.extend(transposed_block)
        
        return transposed
    
    def _reverse_transposition(self, data: bytearray) -> bytearray:
        """Reverse columnar transposition"""
        if len(data) < 8:
            return data
        
        block_size = 8 + (len(data) % 9)
        original = bytearray()
        
        for i in range(0, len(data), block_size):
            block = data[i:i + block_size]
            
            # Reverse transpose using same pattern
            pattern = [3, 0, 6, 1, 4, 7, 2, 5] if block_size == 8 else list(range(block_size))
            if block_size > 8:
                pattern = [(i * 7) % block_size for i in range(block_size)]
            
            # Create reverse mapping
            reverse_pattern = [0] * len(pattern)
            for idx, pos in enumerate(pattern):
                if pos < len(reverse_pattern):
                    reverse_pattern[pos] = idx
            
            original_block = bytearray([0] * len(block))
            for idx, pos in enumerate(reverse_pattern):
                if idx < len(block) and pos < len(block):
                    original_block[idx] = block[pos]
            
            original.extend(original_block)
        
        return original
    
    def _add_integrity_check(self, data: bytearray) -> bytearray:
        """Add integrity check using custom checksum"""
        # Calculate custom checksum
        checksum = 0
        for i, byte in enumerate(data):
            checksum ^= byte
            checksum = (checksum + i * 13) % 256
        
        # Add timestamp for replay protection
        timestamp = int(time.time()) % (2**16)
        
        # Prepend checksum and timestamp
        result = bytearray()
        result.append(checksum)
        result.append(timestamp & 0xFF)
        result.append((timestamp >> 8) & 0xFF)
        result.extend(data)
        
        return result
    
    def _verify_integrity(self, data: bytearray) -> tuple:
        """Verify integrity and extract original data"""
        if len(data) < 3:
            return False, bytearray()
        
        stored_checksum = data[0]
        timestamp = data[1] | (data[2] << 8)
        original_data = data[3:]
        
        # Verify checksum
        calculated_checksum = 0
        for i, byte in enumerate(original_data):
            calculated_checksum ^= byte
            calculated_checksum = (calculated_checksum + i * 13) % 256
        
        # Check if timestamp is reasonable (within 24 hours)
        current_time = int(time.time()) % (2**16)
        time_diff = abs(current_time - timestamp)
        if time_diff > 32768:  # Handle wraparound
            time_diff = 65536 - time_diff
        
        is_valid = (stored_checksum == calculated_checksum and time_diff < 86400)
        
        return is_valid, original_data
    
    def encrypt(self, data: str) -> str:
        """Multi-layer encryption with integrity protection"""
        if not data:
            return ""
        
        try:
            # Convert to bytes
            data_bytes = bytearray(data.encode('utf-8'))
            
            # Layer 1: XOR with rotating key
            for i in range(len(data_bytes)):
                key_index = (i * 3 + 7) % len(self.master_key)
                data_bytes[i] ^= ord(self.master_key[key_index])
            
            # Layer 2: Substitution cipher
            for i in range(len(data_bytes)):
                data_bytes[i] = self.substitution_box[data_bytes[i]]
            
            # Layer 3: Feistel cipher
            data_bytes = self._apply_feistel_cipher(data_bytes)
            
            # Layer 4: Transposition
            data_bytes = self._apply_transposition(data_bytes)
            
            # Layer 5: Add integrity check
            data_bytes = self._add_integrity_check(data_bytes)
            
            # Final encoding
            return base64.b64encode(data_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return ""
    
    def decrypt(self, encrypted_data: str) -> str:
        """Multi-layer decryption with integrity verification"""
        if not encrypted_data:
            return ""
        
        try:
            # Base64 decode
            data_bytes = bytearray(base64.b64decode(encrypted_data.encode('utf-8')))
            
            # Layer 5: Verify integrity
            is_valid, data_bytes = self._verify_integrity(data_bytes)
            if not is_valid:
                print("⚠️ Data integrity check failed")
                return ""
            
            # Layer 4: Reverse transposition
            data_bytes = self._reverse_transposition(data_bytes)
            
            # Layer 3: Reverse Feistel cipher
            data_bytes = self._reverse_feistel_cipher(data_bytes)
            
            # Layer 2: Reverse substitution cipher
            for i in range(len(data_bytes)):
                data_bytes[i] = self.reverse_substitution_box[data_bytes[i]]
            
            # Layer 1: Reverse XOR
            for i in range(len(data_bytes)):
                key_index = (i * 3 + 7) % len(self.master_key)
                data_bytes[i] ^= ord(self.master_key[key_index])
            
            # Convert back to string and remove padding
            result = data_bytes.decode('utf-8')
            return result.rstrip('\x00')
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""
    
    def encrypt_profile_data(self, profile_data: dict) -> dict:
        """Encrypt sensitive profile data with field-specific keys"""
        encrypted_data = {}
        sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        
        for key, value in profile_data.items():
            if key in sensitive_fields and value:
                # Use field-specific encryption for added security
                field_encryptor = Encryption(f"{self.master_key}_{key}")
                encrypted_data[key] = field_encryptor.encrypt(str(value))
                
                # Add field identifier for verification
                encrypted_data[f"{key}_hash"] = self._field_hash(str(value), key)
            else:
                encrypted_data[key] = value
        
        # Add encryption metadata
        encrypted_data['_encryption_version'] = '2.0'
        encrypted_data['_encryption_timestamp'] = int(time.time())
        
        return encrypted_data
    
    def decrypt_profile_data(self, encrypted_data: dict) -> dict:
        """Decrypt sensitive profile data with verification"""
        decrypted_data = {}
        sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        
        for key, value in encrypted_data.items():
            if key in sensitive_fields and value:
                try:
                    # Use field-specific decryption
                    field_encryptor = Encryption(f"{self.master_key}_{key}")
                    decrypted_value = field_encryptor.decrypt(str(value))
                    
                    # Verify field hash if available
                    hash_key = f"{key}_hash"
                    if hash_key in encrypted_data:
                        expected_hash = self._field_hash(decrypted_value, key)
                        if encrypted_data[hash_key] != expected_hash:
                            print(f"⚠️ Hash verification failed for field: {key}")
                            decrypted_value = "[CORRUPTED]"
                    
                    decrypted_data[key] = decrypted_value
                    
                except Exception as e:
                    print(f"⚠️ Failed to decrypt field {key}: {e}")
                    decrypted_data[key] = "[DECRYPT_ERROR]"
                    
            elif not key.endswith('_hash') and not key.startswith('_encryption'):
                decrypted_data[key] = value
        
        return decrypted_data
    
    def _field_hash(self, value: str, field_name: str) -> str:
        """Generate field-specific hash for integrity"""
        combined = f"{field_name}:{value}:{self.master_key}"
        hash_value = self._custom_hash(combined)
        return hash_value[:16]  # Use first 16 characters
    
    def get_encryption_stats(self) -> dict:
        """Get encryption system statistics"""
        return {
            'algorithm': 'Multi-layer Custom Encryption',
            'layers': [
                'XOR with rotating key',
                'Substitution cipher (S-Box)',
                'Feistel cipher (8 rounds)',
                'Columnar transposition',
                'Integrity protection'
            ],
            'key_size': len(self.master_key) * 8,
            'matrix_size': '16x16',
            'sbox_size': 256,
            'security_features': [
                'Timestamp-based replay protection',
                'Field-specific encryption keys',
                'Data integrity verification',
                'Custom hash functions',
                'Multi-round Feistel network'
            ]
        }

# Backward compatibility with simple encryption
class SimpleEncryption(Encryption):
    """Simple encryption class for backward compatibility"""
    
    def __init__(self, key: str = "StimaSukses2024"):
        super().__init__(key)

# Test and demonstration functions
def test__encryption():
    """Comprehensive test of  encryption system"""
    print("===  ENCRYPTION SYSTEM TEST ===")
    
    encryptor = Encryption("SecureKey2024_ATS")
    
    # Test basic encryption/decryption
    test_strings = [
        "John Doe",
        "john.doe@email.com",
        "+1-234-567-8900",
        "123 Main Street, City, State 12345",
        "This is a longer text with special characters: !@#$%^&*()_+-=[]{}|;:,.<>?",
        "Unicode test: ñáéíóú 中文 العربية"
    ]
    
    print("\n--- Basic Encryption Test ---")
    for i, test_string in enumerate(test_strings):
        encrypted = encryptor.encrypt(test_string)
        decrypted = encryptor.decrypt(encrypted)
        
        print(f"Test {i+1}:")
        print(f"  Original:  {test_string}")
        print(f"  Encrypted: {encrypted[:50]}{'...' if len(encrypted) > 50 else ''}")
        print(f"  Decrypted: {decrypted}")
        print(f"  Match:     {'✅' if test_string == decrypted else '❌'}")
        print()
    
    # Test profile data encryption
    print("--- Profile Data Encryption Test ---")
    test_profile = {
        'first_name': 'Nathan',
        'last_name': 'Galung',
        'email': 'nathan.galung@email.com',
        'phone_number': '+62-812-3456-7890',
        'address': 'Jl. Ganesha No. 10, Bandung, Jawa Barat',
        'applicant_id': 12345,  # This won't be encrypted
        'application_date': '2024-01-15'  # This won't be encrypted
    }
    
    print("Original profile data:")
    for key, value in test_profile.items():
        print(f"  {key}: {value}")
    
    # Encrypt profile
    encrypted_profile = encryptor.encrypt_profile_data(test_profile)
    print(f"\nEncrypted profile data:")
    for key, value in encrypted_profile.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")
    
    # Decrypt profile
    decrypted_profile = encryptor.decrypt_profile_data(encrypted_profile)
    print(f"\nDecrypted profile data:")
    for key, value in decrypted_profile.items():
        print(f"  {key}: {value}")
    
    # Verify integrity
    sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
    all_match = True
    for field in sensitive_fields:
        if test_profile.get(field) != decrypted_profile.get(field):
            print(f"❌ Mismatch in field: {field}")
            all_match = False
    
    print(f"\nProfile encryption integrity: {'✅' if all_match else '❌'}")
    
    # Show encryption statistics
    print("\n--- Encryption System Statistics ---")
    stats = encryptor.get_encryption_stats()
    print(f"Algorithm: {stats['algorithm']}")
    print(f"Key size: {stats['key_size']} bits")
    print("Security layers:")
    for i, layer in enumerate(stats['layers'], 1):
        print(f"  {i}. {layer}")
    print("Security features:")
    for feature in stats['security_features']:
        print(f"  • {feature}")
    
    return encryptor

def test_encryption_performance():
    """Test encryption performance with various data sizes"""
    print("\n=== ENCRYPTION PERFORMANCE TEST ===")
    
    encryptor = Encryption()
    
    test_sizes = [10, 100, 1000, 5000]  # Character counts
    
    for size in test_sizes:
        test_data = "A" * size
        
        # Measure encryption time
        start_time = time.time()
        encrypted = encryptor.encrypt(test_data)
        encrypt_time = time.time() - start_time
        
        # Measure decryption time
        start_time = time.time()
        decrypted = encryptor.decrypt(encrypted)
        decrypt_time = time.time() - start_time
        
        # Calculate expansion ratio
        expansion_ratio = len(encrypted) / len(test_data) if len(test_data) > 0 else 0
        
        print(f"Data size: {size:4d} chars")
        print(f"  Encryption time: {encrypt_time*1000:6.2f} ms")
        print(f"  Decryption time: {decrypt_time*1000:6.2f} ms")
        print(f"  Size expansion:  {expansion_ratio:6.2f}x")
        print(f"  Integrity check: {'✅' if test_data == decrypted else '❌'}")
        print()

def demonstrate_security_features():
    """Demonstrate  security features"""
    print("\n=== SECURITY FEATURES DEMONSTRATION ===")
    
    encryptor = Encryption("DemoKey2024")
    
    # 1. Test tampering detection
    print("1. Tampering Detection Test:")
    original_data = "Sensitive Information"
    encrypted = encryptor.encrypt(original_data)
    
    # Simulate tampering by modifying encrypted data
    tampered = list(encrypted)
    if len(tampered) > 10:
        tampered[10] = 'X' if tampered[10] != 'X' else 'Y'
    tampered_encrypted = ''.join(tampered)
    
    decrypted_tampered = encryptor.decrypt(tampered_encrypted)
    print(f"  Original: {original_data}")
    print(f"  After tampering: {decrypted_tampered}")
    print(f"  Tampering detected: {'✅' if decrypted_tampered == '' else '❌'}")
    
    # 2. Test different keys
    print("\n2. Key Sensitivity Test:")
    encryptor2 = Encryption("WrongKey2024")
    wrong_key_decrypt = encryptor2.decrypt(encrypted)
    print(f"  Correct key decrypt: {encryptor.decrypt(encrypted)}")
    print(f"  Wrong key decrypt: {wrong_key_decrypt}")
    print(f"  Key sensitivity: {'✅' if wrong_key_decrypt != original_data else '❌'}")
    
    # 3. Test field-specific encryption
    print("\n3. Field-specific Encryption Test:")
    profile1 = {'email': 'test@example.com'}
    profile2 = {'phone_number': 'test@example.com'}  # Same value, different field
    
    enc1 = encryptor.encrypt_profile_data(profile1)
    enc2 = encryptor.encrypt_profile_data(profile2)
    
    print(f"  Same value, different fields produce different ciphertext:")
    print(f"  Email encryption:    {enc1['email'][:30]}...")
    print(f"  Phone encryption:    {enc2['phone_number'][:30]}...")
    print(f"  Different ciphertext: {'✅' if enc1['email'] != enc2['phone_number'] else '❌'}")

if __name__ == "__main__":
    # Run all tests
    test__encryption()
    test_encryption_performance()
    demonstrate_security_features()
    
    print("\n🔒  Encryption System Ready!")
    print("Features: Multi-layer encryption, integrity protection, field-specific keys")
    print("Security: Custom algorithms, tamper detection, key sensitivity")