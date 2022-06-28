all: rfsoc2x2 zcu111 rfsoc4x2 tarball

rfsoc2x2:
	$(MAKE) -C boards/RFSoC2x2/

zcu111:
	$(MAKE) -C boards/ZCU111/

rfsoc4x2:
	$(MAKE) -C boards/RFSoC4x2/
	
tarball:
	touch rfsoc_sdfec.tar.gz
	tar --exclude='.[^/]*' --exclude="rfsoc_sdfec.tar.gz" -czvf rfsoc_sdfec.tar.gz .
