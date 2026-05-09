//
//  FlycutImageStore.h
//  Flycut
//
//  File-based image storage for clipboard image clippings.
//

#import <Foundation/Foundation.h>
#import <CommonCrypto/CommonDigest.h>

@interface FlycutImageStore : NSObject {
    NSString *imagesDirectoryPath;
}

+(FlycutImageStore *)sharedStore;

-(NSString *)hashForData:(NSData *)data;
-(BOOL)saveImageData:(NSData *)data forHash:(NSString *)hash;
-(NSData *)imageDataForHash:(NSString *)hash;
-(void)deleteImageForHash:(NSString *)hash;
-(BOOL)hasImageForHash:(NSString *)hash;
-(NSString *)imagesDirectoryPath;
-(NSArray *)allStoredHashes;

@end
